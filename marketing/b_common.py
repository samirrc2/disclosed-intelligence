"""
b_common.py — shared helpers for the Paper 10B ("Lawyered vs. Loud") pipeline.

Reuses Paper A's key pool + prompts; adds a polite GENERIC web fetcher (adviser marketing
sites, not SEC) and an LLM classify helper. Paper B runs on the SAME frozen random-400 as A.

Layout (relative to this file, which lives in Paper 10/marketing/):
    ../data/pilot_sample_400.csv          shared frozen sample (crd, firm, type, aum_quartile)
    ../data/brochure_text/current/{crd}.txt  shared brochure text (from A's s03)
    ../pilot/prompts/typology_v1.md          shared typology rubric
    ../pilot/prompts/exposure_fingerprints_v1.md  shared F1-F7 fingerprint
    ../build/common.py                       shared key-pool loader
Outputs stay under marketing/ (data/, out/).
"""
from __future__ import annotations
import os, re, sys, time, json, random, hashlib, threading
from pathlib import Path
import requests

BROOT = Path(__file__).resolve().parent          # .../Paper 10/marketing
P10   = BROOT.parent                              # .../Paper 10
sys.path.insert(0, str(P10 / "build"))
from common import load_key_pools                 # reuse A's key parsing/pool  # noqa: E402

SAMPLE      = P10 / "data" / "pilot_sample_400.csv"
BROCHURE_TXT= P10 / "data" / "brochure_text" / "current"
TYPOLOGY    = P10 / "pilot" / "prompts" / "typology_v1.md"
FINGERPRINT = P10 / "pilot" / "prompts" / "exposure_fingerprints_v1.md"
BDATA = BROOT / "data";  BOUT = BROOT / "out";  BRAW = BDATA / "raw"
for d in (BDATA, BOUT, BRAW, BDATA / "marketing_text"):
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ polite generic web fetch
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
_sess = requests.Session()
_sess.headers.update({"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*"})
_last: dict[str, float] = {}
_lock = threading.Lock()
MIN_INTERVAL = 1.0

def web_get(url: str, timeout: int = 20):
    from urllib.parse import urlparse
    host = urlparse(url).netloc
    with _lock:
        wait = MIN_INTERVAL - (time.time() - _last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.time()
    try:
        r = _sess.get(url, timeout=timeout, allow_redirects=True)
        return r
    except requests.RequestException:
        return None

def persist_raw_b(subdir: str, name: str, content: bytes, url: str = "") -> Path:
    d = BRAW / subdir; d.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(content).hexdigest()
    p = d / name
    if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == sha:
        return p
    p.write_bytes(content)
    with open(BRAW / "MANIFEST.csv", "a") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},{subdir}/{name},{sha},{len(content)},{url}\n")
    return p

# ------------------------------------------------------------------ LLM classify (OpenAI-compatible)
SPEND = {"usd": 0.0}
PRICE = {"gpt-4o": (2.5, 10.0), "gpt-4o-mini": (0.15, 0.60), "gpt-5-mini": (0.25, 2.0),
         "gemini-2.0-flash": (0.10, 0.40)}
_pools = None
def pools():
    global _pools
    if _pools is None:
        _pools = load_key_pools()
    return _pools

def call_llm(provider, model, base_url, system, user, budget=30.0):
    from openai import OpenAI
    if SPEND["usd"] >= budget:
        raise RuntimeError(f"budget ${budget} reached")
    pool = pools().get(provider)
    if not pool:
        raise SystemExit(f"no usable key for {provider} in keys.env.txt")
    while True:
        key = pool.get()
        try:
            client = (OpenAI(api_key=key, base_url=base_url, timeout=60.0, max_retries=1)
                      if base_url else OpenAI(api_key=key, timeout=60.0, max_retries=1))
            kw = dict(model=model, temperature=0,
                      messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
            try:
                r = client.chat.completions.create(response_format={"type": "json_object"}, **kw)
            except Exception as e1:
                if "response_format" in str(e1).lower() or "json" in str(e1).lower():
                    r = client.chat.completions.create(**kw)
                else:
                    raise
            u = r.usage; pin, pout = PRICE.get(model, (1.0, 3.0))
            SPEND["usd"] += (u.prompt_tokens * pin + u.completion_tokens * pout) / 1e6
            return r.choices[0].message.content
        except Exception as e:
            m = str(e).lower()
            if "429" in m or "rate" in m or "quota" in m:
                pool.bench(key); continue
            raise

def parse_json(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lstrip().lower().startswith("json"):
            raw = raw.lstrip()[4:]
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
        raise

# ------------------------------------------------------------------ stats
def bootstrap_ci(diffs, iters=2000, seed=42):
    diffs = [d for d in diffs if d is not None]
    if not diffs:
        return (None, None, None)
    rng = random.Random(seed); n = len(diffs); means = []
    for _ in range(iters):
        s = sum(diffs[rng.randrange(n)] for _ in range(n)) / n
        means.append(s)
    means.sort()
    return (sum(diffs) / n, means[int(0.025 * iters)], means[int(0.975 * iters)])
