"""
b03_classify_marketing.py — classify marketing text (typology + exposure) AND run the exposure
fingerprint on the BROCHURE text at full scale (Paper A only did exposure at pilot n=59).

Reuses the frozen typology rubric and the F1-F7 enforcement fingerprint from ../pilot/prompts.
Same LLM family as A (default gpt-4o; override with MODEL env). Hard budget guard.

Outputs (marketing/out/):
    marketing_labels.csv     crd,a,b,c,d,e
    marketing_exposure.csv   crd,exposed,fingerprints
    brochure_exposure.csv    crd,exposed,fingerprints   (full-scale, all firms with a brochure)

Usage:  python b03_classify_marketing.py
"""
import os, re, csv, glob
from pathlib import Path
from b_common import (BDATA, BOUT, BROCHURE_TXT, TYPOLOGY, FINGERPRINT,
                      call_llm, parse_json, SPEND)

MODEL = os.environ.get("MODEL", "gpt-4o")
PROVIDER = os.environ.get("PROVIDER", "OPENAI_API_KEY")
BASE_URL = os.environ.get("BASE_URL", "https://api.openai.com/v1")
BUDGET = float(os.environ.get("BUDGET", "30"))
MTXT = BDATA / "marketing_text"

KW = re.compile(r"artificial intelligence|\bAI\b|machine learning|deep learning|neural|generative|"
                r"large language|LLM|natural language|algorithm|quantitative model|model-driven|"
                r"predictive|automated|robo|data science", re.I)

def window(text, radius=340, cap=40):
    hits = [m.start() for m in KW.finditer(text)]
    if not hits:
        return "(NO AI/TECH KEYWORDS)\n\n" + text[:1500]
    spans = sorted((max(0, h - radius), min(len(text), h + radius)) for h in hits)
    merged = [spans[0]]
    for s, e in spans[1:]:
        if s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return "\n...\n".join(text[s:e] for s, e in merged[:cap])

TYP_SYS = TYPOLOGY.read_text() + ('\n\nReturn ONLY JSON: '
          '{"a":0|1,"b":0|1,"c":0|1,"d":0|1,"e":0|1}')
EXP_SYS = FINGERPRINT.read_text() + ('\n\nJudge the FILING FIRM\'S OWN claims in the supplied text '
          'against fingerprints F1-F7. Distinguish promotional claims materially similar to the '
          'charged conduct from neutral factual automation disclosure and hedged risk language. '
          'Return ONLY JSON: {"exposed":true|false,"fingerprints":["F3",...],"quote":"<verbatim or \'\'>"}')

def classify_typology(text):
    raw = call_llm(PROVIDER, MODEL, BASE_URL, TYP_SYS, window(text), BUDGET)
    j = parse_json(raw)
    return {L: int(j.get(L, 0) or 0) for L in "abcde"}

def classify_exposure(text):
    raw = call_llm(PROVIDER, MODEL, BASE_URL, EXP_SYS, window(text), BUDGET)
    j = parse_json(raw)
    return int(bool(j.get("exposed"))), ";".join(j.get("fingerprints", []) or [])

def run(kind, files, do_typology):
    lab_rows, exp_rows = [], []
    n = len(files)
    for i, f in enumerate(files):
        crd = int(Path(f).stem)
        text = Path(f).read_text(encoding="utf-8", errors="replace")
        try:
            if do_typology:
                lab = classify_typology(text); lab_rows.append({"crd": crd, **lab})
            ex, fps = classify_exposure(text); exp_rows.append({"crd": crd, "exposed": ex, "fingerprints": fps})
        except Exception as e:
            print(f"[b03/{kind}] {i+1}/{n} crd={crd} ERROR {str(e)[:70]}", flush=True)
            if "budget" in str(e).lower():
                break
            continue
        if (i + 1) % 25 == 0:
            print(f"[b03/{kind}] {i+1}/{n}  spend=${SPEND['usd']:.2f}", flush=True)
    return lab_rows, exp_rows

def write(path, rows, cols):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)

def main():
    mkt = sorted(glob.glob(str(MTXT / "*.txt")))
    print(f"[b03] marketing: {len(mkt)} firms | model {MODEL} | budget ${BUDGET}", flush=True)
    lab, exp = run("mkt", mkt, do_typology=True)
    write(BOUT / "marketing_labels.csv", lab, ["crd", "a", "b", "c", "d", "e"])
    write(BOUT / "marketing_exposure.csv", exp, ["crd", "exposed", "fingerprints"])

    bro = sorted(glob.glob(str(BROCHURE_TXT / "*.txt")))
    print(f"[b03] brochure exposure (full scale): {len(bro)} firms", flush=True)
    _, bexp = run("bro", bro, do_typology=False)
    write(BOUT / "brochure_exposure.csv", bexp, ["crd", "exposed", "fingerprints"])
    print(f"[b03] done. total spend ${SPEND['usd']:.2f}. -> marketing/out/*.csv")

if __name__ == "__main__":
    main()
