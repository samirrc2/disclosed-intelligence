"""
common.py — shared backbone for the Paper 10 full-build pipeline.

Provides:
  - config (paths, User-Agent, rate limits)
  - a polite SEC/IAPD HTTP session (identified UA, >=1s throttle per host, backoff on 429/5xx)
  - append-only raw persistence with SHA-256 (never overwrites)
  - an API key pool loader implementing NIW/API Keys/keys.env.txt semantics
    (numbered pools, round-robin, bench-on-429/quota, fail over, abort only when all benched)

Run nothing here directly; it is imported by s01..s06.
Python 3.9+.  pip install -r requirements.txt
"""
from __future__ import annotations
import os, re, csv, time, json, hashlib, threading, itertools, random
from pathlib import Path
from urllib.parse import urlparse
import requests

# ----------------------------------------------------------------------------- paths
ROOT = Path(__file__).resolve().parent.parent          # .../Paper 10
DATA = ROOT / "data"
RAW  = DATA / "raw"
BUILD_OUT = ROOT / "build" / "out"
for d in (DATA, RAW, BUILD_OUT):
    d.mkdir(parents=True, exist_ok=True)

# keys.env.txt lives in an "API Keys" folder under the NIW root, an ancestor of
# this file. Search upward so the loader works regardless of how deeply the
# pipeline/ tree is nested (e.g. Paper 10/pipeline/build/common.py).
def _find_keys_file() -> Path:
    for anc in Path(__file__).resolve().parents:
        cand = anc / "API Keys" / "keys.env.txt"
        if cand.exists():
            return cand
    return ROOT.parent.parent / "API Keys" / "keys.env.txt"  # fallback (may not exist)
KEYS_FILE = _find_keys_file()

# ----------------------------------------------------------------------------- identity / politeness
# SEC fair-access policy REQUIRES a descriptive User-Agent with contact info.
USER_AGENT = "Paper10 Research (Samir Chincholikar) samir.chincholikar@gmail.com"
MIN_INTERVAL_SEC = 1.1          # >= 1s between requests to the same host (SEC asks <=10/s; we go slow)
MAX_RETRIES = 5
BACKOFF_BASE = 2.0

_last_hit: dict[str, float] = {}
_hit_lock = threading.Lock()

def _throttle(host: str):
    with _hit_lock:
        now = time.time()
        wait = MIN_INTERVAL_SEC - (now - _last_hit.get(host, 0.0))
        if wait > 0:
            time.sleep(wait)
        _last_hit[host] = time.time()

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"})

# adviserinfo.sec.gov sits behind Cloudflare and 404s requests that lack browser headers.
# Use a browser UA + Referer for those hosts (contact kept in a From header for politeness);
# keep the SEC-required descriptive UA for www.sec.gov / EDGAR.
_BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
_ADVISERINFO_HEADERS = {
    "User-Agent": _BROWSER_UA,
    "Referer": "https://adviserinfo.sec.gov/",
    "Accept": "application/pdf,application/json,text/html,*/*",
    "From": "samir.chincholikar@gmail.com",
}

def sec_get(url: str, *, stream: bool = False, timeout: int = 60, expect: str | None = None) -> requests.Response:
    """Polite GET for sec.gov / adviserinfo hosts. Retries on 429/5xx with backoff.
    expect='pdf'|'json'|None -> light content sanity check (raises on obvious HTML error page)."""
    host = urlparse(url).netloc
    headers = _ADVISERINFO_HEADERS if "adviserinfo.sec.gov" in host else {"User-Agent": USER_AGENT}
    for attempt in range(1, MAX_RETRIES + 1):
        _throttle(host)
        try:
            r = _session.get(url, stream=stream, timeout=timeout, headers=headers)
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(BACKOFF_BASE ** attempt)
            continue
        if r.status_code == 200:
            if expect == "pdf" and not r.content[:5].startswith(b"%PDF") and not stream:
                # some brochures come back as HTML error; signal caller
                r._not_pdf = True  # type: ignore
            return r
        if r.status_code in (403, 404):
            return r  # let caller record as not_found/blocked; do not hammer
        # 429 / 5xx -> back off
        time.sleep(BACKOFF_BASE ** attempt + random.random())
    return r  # type: ignore

# ----------------------------------------------------------------------------- append-only raw persistence
MANIFEST = RAW / "MANIFEST.csv"

def _manifest_row(name, sha, nbytes, url):
    new = not MANIFEST.exists()
    with open(MANIFEST, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["saved_utc", "filename", "sha256", "bytes", "source_url"])
        w.writerow([time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), name, sha, nbytes, url])

def persist_raw(subdir: str, name: str, content: bytes, url: str = "") -> Path:
    """Write bytes append-only under data/raw/<subdir>/<name>.
    Never overwrites: if the same name exists with a DIFFERENT hash, a -vN suffix is added.
    Returns the path actually written (or the existing identical file)."""
    d = RAW / subdir
    d.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(content).hexdigest()
    target = d / name
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() == sha:
            return target  # identical, idempotent
        stem, suf = os.path.splitext(name)
        n = 1
        while (d / f"{stem}-v{n}{suf}").exists():
            n += 1
        target = d / f"{stem}-v{n}{suf}"
    target.write_bytes(content)
    _manifest_row(str(target.relative_to(RAW)), sha, len(content), url)
    return target

# ----------------------------------------------------------------------------- API key pool (keys.env.txt semantics)
def _load_env_file(path: Path) -> dict[str, str]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out

_PLACEHOLDER = re.compile(r"^(AIza\.\.\.|sk-\.\.\.|your[_-]?key|xxx+|\.\.\.)$", re.I)

def _is_real(v: str) -> bool:
    return bool(v) and not _PLACEHOLDER.match(v) and len(v) > 12

class KeyPool:
    """Round-robin pool with bench-on-429/quota and automatic failover.
    A bare NAME with no suffix counts as _1. Placeholders/blanks skipped."""
    def __init__(self, provider: str, keys: list[str]):
        self.provider = provider
        self.keys = keys
        self._benched: set[str] = set()
        self._cycle = itertools.cycle(keys) if keys else None
        self._lock = threading.Lock()

    def __bool__(self):
        return bool([k for k in self.keys if k not in self._benched])

    def get(self) -> str:
        with self._lock:
            live = [k for k in self.keys if k not in self._benched]
            if not live:
                raise RuntimeError(f"[{self.provider}] all {len(self.keys)} keys benched (429/quota).")
            # round robin over live keys
            for _ in range(len(self.keys)):
                k = next(self._cycle)
                if k in live:
                    return k
            return live[0]

    def bench(self, key: str):
        with self._lock:
            self._benched.add(key)
            print(f"[{self.provider}] benched a key ({len(self._benched)}/{len(self.keys)} down)")

def load_key_pools(path: Path = KEYS_FILE) -> dict[str, KeyPool]:
    env = _load_env_file(path)
    # also export to os.environ for SDKs that read env directly
    groups: dict[str, list[str]] = {}
    for k, v in env.items():
        if not _is_real(v):
            continue
        m = re.match(r"^(.*?)(?:_(\d+))?$", k)   # strip trailing _N
        base = m.group(1)
        groups.setdefault(base, []).append((int(m.group(2) or 1), v))
    pools = {}
    for base, kv in groups.items():
        keys = [v for _, v in sorted(kv)]
        pools[base] = KeyPool(base, keys)
    return pools

if __name__ == "__main__":
    p = load_key_pools()
    print("Key file:", KEYS_FILE, "exists=", KEYS_FILE.exists())
    for name, pool in p.items():
        print(f"  {name}: {len(pool.keys)} usable key(s)")
    print("User-Agent:", USER_AGENT)
