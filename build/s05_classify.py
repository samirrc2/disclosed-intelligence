"""
s05_classify.py — classify every retrieved brochure with the frozen typology, using the
provided API keys (real cross-family validation this time).

  - PRIMARY classifier: an OpenAI frontier-mini model (default gpt-4o-mini; set PRIMARY_MODEL).
  - SECOND FAMILY validation: a 60-firm random subsample re-classified by a different family
    (default xAI Grok via its OpenAI-compatible endpoint; or Gemini). Per-label agreement + kappa.
  - Key pools loaded from NIW/API Keys/keys.env.txt with round-robin + 429 failover.
  - Cost ledger with HARD ABORT at $30 (classification-tooling budget).

Prompt is read verbatim from pilot/prompts/typology_v1.md (the versioned instrument).

Outputs:
  pilot/labels_primary.csv, pilot/labels_secondary_sub.csv,
  pilot/validation_agreement.json, pilot/COST_LEDGER_live.csv

Usage:  python s05_classify.py
"""
import os, re, csv, json, glob, random, time
from pathlib import Path
from common import load_key_pools, ROOT, DATA

TXT_DIR = DATA / "brochure_text" / "current"
PROMPT_FILE = ROOT / "pilot" / "prompts" / "typology_v1.md"
OUT = ROOT / "pilot"
BUDGET_USD = 30.0
SEED = 42
VALIDATION_N = 60

PRIMARY = {"provider": "OPENAI_API_KEY", "model": os.environ.get("PRIMARY_MODEL", "gpt-4o-mini"),
           "base_url": "https://api.openai.com/v1"}
# second family — Gemini via its OpenAI-compatible endpoint (a different model family = valid
# cross-family check). Override with env vars if a model name differs on your account.
SECONDARY = {"provider": os.environ.get("SECONDARY_PROVIDER", "GEMINI_API_KEY"),
             "model": os.environ.get("SECONDARY_MODEL", "gemini-2.0-flash"),
             "base_url": os.environ.get("SECONDARY_BASE_URL",
                                        "https://generativelanguage.googleapis.com/v1beta/openai/")}

# rough $/1M tokens (in,out) — adjust to current pricing; used only for the abort guard
PRICE = {"gpt-4o-mini": (0.15, 0.60), "gpt-5-mini": (0.25, 2.0),
         "grok-4": (3.0, 15.0), "grok-3": (3.0, 15.0),
         "gemini-2.0-flash": (0.10, 0.40), "gemini-2.5-flash": (0.30, 2.5), "gemini-1.5-flash": (0.075, 0.30)}

pools = load_key_pools()
_spend = {"usd": 0.0}

def ai_window(text: str, radius: int = 320) -> str:
    """Send only AI-relevant windows (recall-friendly, cheap). Falls back to head of doc."""
    kws = re.compile(r"artificial intelligence|\bAI\b|machine learning|deep learning|neural|"
                     r"generative|large language|LLM|natural language|algorithm|quantitative model|"
                     r"model-driven|predictive|automated|robo|data science", re.I)
    hits = [m.start() for m in kws.finditer(text)]
    if not hits:
        return "(NO AI/TECH KEYWORDS FOUND IN BROCHURE)\n\n" + text[:1500]
    spans, out = [], []
    for h in hits:
        spans.append((max(0, h - radius), min(len(text), h + radius)))
    # merge overlapping
    spans.sort(); merged = [spans[0]]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    for s, e in merged[:40]:
        out.append(text[s:e])
    return "\n...\n".join(out)

def call_llm(cfg, system, user):
    from openai import OpenAI
    pool = pools.get(cfg["provider"])
    if not pool:
        raise SystemExit(f"[s05] no usable key for {cfg['provider']} in keys.env.txt")
    while True:
        key = pool.get()
        try:
            client = (OpenAI(api_key=key, base_url=cfg["base_url"], timeout=60.0, max_retries=1)
                      if cfg["base_url"] else OpenAI(api_key=key, timeout=60.0, max_retries=1))
            kw = dict(model=cfg["model"], temperature=0,
                      messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
            try:
                r = client.chat.completions.create(response_format={"type": "json_object"}, **kw)
            except Exception as e1:
                if "response_format" in str(e1).lower() or "json" in str(e1).lower():
                    r = client.chat.completions.create(**kw)   # provider rejects JSON mode -> plain
                else:
                    raise
            u = r.usage
            pin, pout = PRICE.get(cfg["model"], (1.0, 3.0))
            _spend["usd"] += (u.prompt_tokens * pin + u.completion_tokens * pout) / 1e6
            return r.choices[0].message.content
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "rate" in msg or "quota" in msg:
                pool.bench(key); continue
            raise

def classify(cfg, crd, firm, text):
    system = PROMPT_FILE.read_text()
    system += ('\n\nReturn ONLY JSON: {"crd":int,"a":0|1,"b":0|1,"c":0|1,"d":0|1,"e":0|1,'
               '"evidence":{"a":"","b":"","c":"","d":"","e":""}}')
    user = f"CRD {crd} — {firm}\nBrochure AI-relevant excerpts:\n{ai_window(text)}"
    raw = call_llm(cfg, system, user)
    j = _parse_json(raw); j["crd"] = crd
    for L in "abcde":
        j[L] = int(j.get(L, 0) or 0)
    return j

def _parse_json(raw: str):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lstrip().lower().startswith("json"):
            raw = raw.lstrip()[4:]
    try:
        return json.loads(raw)
    except Exception:
        import re
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
        raise

def kappa(pairs):
    n = len(pairs); po = sum(x == y for x, y in pairs) / n
    p1a = sum(x for x, _ in pairs) / n; p1b = sum(y for _, y in pairs) / n
    pe = p1a * p1b + (1 - p1a) * (1 - p1b)
    return po, (1.0 if pe == 1 else (po - pe) / (1 - pe))

def main():
    files = sorted(glob.glob(str(TXT_DIR / "*.txt")))
    if not files:
        raise SystemExit("[s05] no brochure text — run s03 first.")
    print(f"[s05] classifying {len(files)} brochures with {PRIMARY['model']} (budget ${BUDGET_USD})", flush=True)
    # resume: reload any firms already classified
    primary = {}
    pfile = OUT / "labels_primary.csv"
    if pfile.exists():
        import pandas as pd
        prev = pd.read_csv(pfile)
        for _, r in prev.iterrows():
            primary[int(r["crd"])] = {k: int(r[k]) for k in ["a", "b", "c", "d", "e"]}
        print(f"[s05] resuming: {len(primary)} firms already done", flush=True)
    n = len(files)
    with open(pfile, "a", newline="") as fh:
        w = csv.writer(fh)
        if pfile.stat().st_size == 0:
            w.writerow(["crd", "a", "b", "c", "d", "e"])
        for i, f in enumerate(files):
            crd = int(Path(f).stem)
            if crd in primary:
                continue
            if _spend["usd"] >= BUDGET_USD:
                print(f"[s05] ABORT: budget ${BUDGET_USD} reached at firm {i}."); break
            text = Path(f).read_text(encoding="utf-8", errors="replace")
            try:
                j = classify(PRIMARY, crd, "", text)
            except Exception as e:
                print(f"[s05] {i+1}/{n} crd={crd} ERROR {str(e)[:80]}", flush=True); continue
            primary[crd] = j
            w.writerow([crd, j["a"], j["b"], j["c"], j["d"], j["e"]]); fh.flush()
            print(f"[s05] {i+1}/{n} crd={crd} -> a{j['a']}b{j['b']}c{j['c']}d{j['d']}e{j['e']}  ${_spend['usd']:.2f}", flush=True)

    # ---- second-family validation on 60-firm subsample ----
    random.seed(SEED)
    sub = random.sample(list(primary), min(VALIDATION_N, len(primary)))
    print(f"[s05] validating {len(sub)} firms with {SECONDARY['model']} ({SECONDARY['provider']})")
    secondary = {}
    with open(OUT / "labels_secondary_sub.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["crd", "a", "b", "c", "d", "e"])
        for crd in sub:
            if _spend["usd"] >= BUDGET_USD:
                print("[s05] ABORT during validation (budget)."); break
            text = (TXT_DIR / f"{crd}.txt").read_text(encoding="utf-8", errors="replace")
            try:
                j = classify(SECONDARY, crd, "", text)
            except Exception as e:
                print(f"[s05] sec {crd} error {e}"); continue
            secondary[crd] = j; w.writerow([crd, j["a"], j["b"], j["c"], j["d"], j["e"]])

    agree = {}
    common = [c for c in sub if c in secondary]
    for L in ["a", "b", "c", "d", "e"]:
        pairs = [(primary[c][L], secondary[c][L]) for c in common]
        po, k = kappa(pairs) if pairs else (None, None)
        agree[L] = {"pct": po, "kappa": k, "n": len(pairs)}
    json.dump({"validation": agree, "spend_usd": round(_spend["usd"], 4), "n_primary": len(primary)},
              open(OUT / "validation_agreement.json", "w"), indent=1)
    print("[s05] validation:", json.dumps(agree, indent=1))
    print(f"[s05] total metered spend: ${_spend['usd']:.2f} of ${BUDGET_USD}")

if __name__ == "__main__":
    main()
