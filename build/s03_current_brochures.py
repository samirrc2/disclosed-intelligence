"""
s03_current_brochures.py — retrieve each sampled firm's CURRENT Part 2A BROCHURE(S).

FIX: the /reports/ADV/{CRD}/PDF/{CRD}.pdf endpoint returns the Part 1 registration form
(structured checkboxes), NOT the narrative brochure. The brochure lives behind its version id.
Correct path:
  1. GET api.adviserinfo.sec.gov/search/firm/{CRD}
     -> hits.hits[0]._source.iacontent  (a JSON *string*)
     -> json.loads it -> brochures.brochuredetails[*].brochureVersionID
  2. GET files.adviserinfo.sec.gov/.../crd_iapd_Brochure.aspx?BRCHR_VRSN_ID={vid}  (the PDF)
A firm may file several brochures (e.g. one per program); we pull and concatenate all of them.

Outputs:
    data/raw/brochures/{crd}_{vid}.pdf        (append-only, hashed)
    data/brochure_text/current/{crd}.txt      (concatenated brochure text)
    build/out/current_retrieval_log.csv

Usage:  python s03_current_brochures.py
"""
import csv, io, json
import pandas as pd
from pathlib import Path
from common import sec_get, persist_raw, DATA, BUILD_OUT

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

SAMPLE = DATA / "pilot_sample_400.csv"
TXT_DIR = DATA / "brochure_text" / "current"
TXT_DIR.mkdir(parents=True, exist_ok=True)
LOG = BUILD_OUT / "current_retrieval_log.csv"

API    = "https://api.adviserinfo.sec.gov/search/firm/{crd}"
VIEWER = "https://files.adviserinfo.sec.gov/IAPD/Content/Common/crd_iapd_Brochure.aspx?BRCHR_VRSN_ID={vid}"
MAX_PAGES = 150
MAX_BROCHURES = 8

def _pdf_text(content: bytes) -> str:
    if fitz is not None:
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            parts = [pg.get_text() for i, pg in enumerate(doc) if i < MAX_PAGES]
            doc.close()
            return "\n".join(parts)
        except Exception:
            pass
    if pdfplumber is not None:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join((pg.extract_text() or "") for i, pg in enumerate(pdf.pages) if i < MAX_PAGES)
    raise SystemExit("pip install pymupdf (or pdfplumber)")

def _brochure_list(crd: int):
    """Return [(version_id, date), ...] for the firm's current brochures."""
    r = sec_get(API.format(crd=crd), expect="json", timeout=30)
    if r.status_code != 200:
        return [], f"api_{r.status_code}"
    try:
        src = r.json()["hits"]["hits"][0]["_source"]["iacontent"]   # nested JSON string
        data = json.loads(src)
        det = (data.get("brochures") or {}).get("brochuredetails") or []
        out = [(str(b["brochureVersionID"]), b.get("dateSubmitted", "")) for b in det if b.get("brochureVersionID")]
        exempt = (data.get("brochures") or {}).get("part2ExemptFlag") == "Y"
        return out, ("part2_exempt" if (not out and exempt) else "ok")
    except Exception as e:
        return [], f"parse_err:{type(e).__name__}"

def fetch_one(crd: int):
    brs, note = _brochure_list(crd)
    if not brs:
        return None, note, None
    texts, dt = [], brs[0][1]
    for vid, _ in brs[:MAX_BROCHURES]:
        r = sec_get(VIEWER.format(vid=vid), expect="pdf", timeout=30)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            persist_raw("brochures", f"{crd}_{vid}.pdf", r.content, VIEWER.format(vid=vid))
            try:
                texts.append(_pdf_text(r.content))
            except Exception:
                pass
    if not texts:
        return None, "viewer_no_pdf", dt
    return "\n\n=== BROCHURE BREAK ===\n\n".join(texts), f"ok({len(texts)}br)", dt

def main():
    if not SAMPLE.exists():
        raise SystemExit("[s03] run s02_sample.py first.")
    df = pd.read_csv(SAMPLE)
    rows, n = [], len(df)
    print(f"[s03] retrieving brochures for {n} firms (live; cached skip instantly)", flush=True)
    for i, rec in df.iterrows():
        crd = int(rec["crd"])
        txt_path = TXT_DIR / f"{crd}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 0:
            rows.append({"crd": crd, "status": "cached", "chars": txt_path.stat().st_size})
            print(f"[s03] {i+1}/{n} crd={crd} cached", flush=True); continue
        try:
            text, how, dt = fetch_one(crd)
        except Exception as e:
            rows.append({"crd": crd, "status": f"error:{type(e).__name__}", "chars": 0})
            print(f"[s03] {i+1}/{n} crd={crd} ERROR {type(e).__name__}", flush=True); continue
        if not text:
            rows.append({"crd": crd, "status": how, "chars": 0, "date": ""})
            print(f"[s03] {i+1}/{n} crd={crd} {how}", flush=True); continue
        txt_path.write_text(text, encoding="utf-8")
        rows.append({"crd": crd, "status": how, "chars": len(text), "date": dt})
        print(f"[s03] {i+1}/{n} crd={crd} {how} ({len(text)} chars)", flush=True)
    with open(LOG, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["crd", "status", "chars", "date"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in ["crd", "status", "chars", "date"]})
    ok = sum(1 for r in rows if str(r["status"]).startswith(("ok", "cached")))
    nobr = sum(1 for r in rows if r["status"] in ("part2_exempt", "no_brochure"))
    print(f"[s03] retrieved {ok}/{n} = {ok/n:.1%}  (no-brochure/exempt: {nobr})  -> {LOG}")

if __name__ == "__main__":
    main()
