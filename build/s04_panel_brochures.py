"""
s04_panel_brochures.py — OPTIONAL light trend point (one prior-year snapshot).

This step is NOT required for the paper. The current cross-section (s03/s05/s06) is the spine.
Run this only if you want a single 2024 vs 2026 comparison to show AI disclosure emerging.
It downloads SEC's bulk Part 2 archive for one year (still a few hundred MB); skip it to stay lean.

--- original purpose retained below ---
s04_panel_brochures.py — THE PANEL CONFIRMATION (E4).

The IAPD API serves only the CURRENT brochure (verified), so historical brochures (2021-2025)
must come from SEC's bulk Form ADV Part 2 monthly archives. This script:
  1. Discovers the Part 2 (brochure) ZIP links on SEC's Form ADV Data page.
  2. Downloads ONE snapshot per target year (append-only, hashed).
  3. Inspects each ZIP's internal structure and prints it (folder layout, sample PDF names,
     any index/manifest CSVs) so the CRD<->brochure mapping can be wired.
  4. If an index is present, maps sampled CRDs -> brochure PDFs and reports PER-YEAR COVERAGE.
     Coverage >=50% for 2023-and-earlier => PANEL paper; else DOWNGRADE to cross-section.

NOTE: SEC's Part 2 bulk files are large (each ~hundreds of MB to GB, March splits into ~8-10
parts) and their internal naming has changed over time. Steps 1-3 always work; step 4's mapping
may need a one-line tweak once you see the printed structure. This is the documented "inspect
and adjust" spot.

Usage:  python s04_panel_brochures.py
        # edit TARGET_YEARS / MONTH_PREF and, after first run, PART2_URLS if needed
"""
import io, re, zipfile, csv
import pandas as pd
from pathlib import Path
from common import sec_get, persist_raw, DATA, BUILD_OUT

FORM_ADV_DATA_PAGE = "https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data"
SAMPLE = DATA / "pilot_sample_400.csv"
PANEL_DIR = DATA / "raw" / "panel"
PANEL_DIR.mkdir(parents=True, exist_ok=True)
LOG = BUILD_OUT / "panel_coverage.csv"

TARGET_YEARS = [2024]     # OPTIONAL single lookback vs the current cross-section (s03).
                          # AI language is ~absent pre-2023, so one prior snapshot is enough
                          # to show the 2024->2026 emergence. Add years here only if a referee
                          # asks for a fuller panel.
MONTH_PREF = "mar"                           # annual amendments cluster in March

# If auto-discovery misses, hardcode confirmed Part 2 zip URLs here {year: [urls...]}:
PART2_URLS: dict[int, list[str]] = {}

def discover_part2_links():
    r = sec_get(FORM_ADV_DATA_PAGE)
    links = re.findall(r'href="([^"]+\.zip)"', r.text)
    out = {}
    for l in links:
        if l.startswith("/"):
            l = "https://www.sec.gov" + l
        low = l.lower()
        if "part2" in low or "brochure" in low:
            y = re.search(r"(20\d{2})", low)
            if y:
                out.setdefault(int(y.group(1)), []).append(l)
    print("[s04] discovered Part 2 brochure links by year:")
    for y in sorted(out):
        print(f"   {y}: {out[y]}")
    return out

def inspect_zip(content: bytes, label: str):
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        names = zf.namelist()
        pdfs = [n for n in names if n.lower().endswith(".pdf")]
        idx  = [n for n in names if n.lower().endswith((".csv", ".txt", ".xml")) ]
        print(f"[s04] {label}: {len(names)} entries, {len(pdfs)} PDFs, {len(idx)} index-like files")
        print("      sample PDF names:", pdfs[:5])
        print("      index files:", idx[:5])
        return zf, names, pdfs, idx

def map_coverage(zf, names, pdfs, idx, crds):
    """Best-effort: match sampled CRDs to brochures in this snapshot.
    Strategy A: an index file mapping CRD/filingid -> pdf. Strategy B: CRD appears in the pdf
    filename. Prints which worked."""
    crds = set(int(c) for c in crds)
    found = set()
    # Strategy B first (cheap): CRD embedded in filename
    for n in pdfs:
        m = re.search(r"(\d{4,7})", Path(n).stem)
        if m and int(m.group(1)) in crds:
            found.add(int(m.group(1)))
    if found:
        print(f"[s04]   matched {len(found)} via filename-embedded CRD")
        return found
    # Strategy A: parse an index file for a CRD column + a pdf reference
    for ix in idx:
        try:
            data = zf.read(ix)
            df = pd.read_csv(io.BytesIO(data), encoding="latin-1", dtype=str, on_bad_lines="skip")
        except Exception:
            continue
        crd_col = next((c for c in df.columns if "crd" in c.lower()), None)
        if crd_col:
            hit = set(pd.to_numeric(df[crd_col], errors="coerce").dropna().astype(int)) & crds
            print(f"[s04]   index {ix}: CRD col {crd_col!r}, {len(hit)} sample firms present")
            found |= hit
    if not found:
        print("[s04]   NO automatic mapping — inspect the printed structure and set the mapping.")
    return found

def main():
    if not SAMPLE.exists():
        raise SystemExit("[s04] run s02_sample.py first.")
    crds = pd.read_csv(SAMPLE)["crd"].tolist()
    links = PART2_URLS or discover_part2_links()
    results = []
    for year in TARGET_YEARS:
        urls = links.get(year, [])
        urls = [u for u in urls if MONTH_PREF in u.lower()] or urls
        if not urls:
            print(f"[s04] {year}: no Part 2 url found; set PART2_URLS[{year}]");
            results.append({"year": year, "coverage": None, "note": "no url"}); continue
        year_found, considered = set(), 0
        for u in urls:
            print(f"[s04] {year}: downloading {u}")
            r = sec_get(u, stream=True, timeout=1800)
            if r.status_code != 200:
                print(f"[s04]   HTTP {r.status_code}"); continue
            content = r.content
            persist_raw("panel", Path(u).name, content, u)
            zf, names, pdfs, idx = inspect_zip(content, f"{year}/{Path(u).name}")
            year_found |= map_coverage(zf, names, pdfs, idx, crds)
            considered += 1
        cov = len(year_found) / len(crds) if crds else 0
        print(f"[s04] {year}: coverage {len(year_found)}/{len(crds)} = {cov:.1%}")
        results.append({"year": year, "coverage": round(cov, 4), "n_found": len(year_found), "parts": considered})
    with open(LOG, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "coverage", "n_found", "parts", "note"])
        w.writeheader()
        for r in results: w.writerow({k: r.get(k, "") for k in ["year","coverage","n_found","parts","note"]})
    print(f"\n[s04] per-year coverage -> {LOG}")
    early = [r["coverage"] for r in results if r["year"] <= 2023 and r.get("coverage") is not None]
    if early:
        verdict = "PANEL (>=50% for <=2023)" if min(early) >= 0.5 else "DOWNGRADE to cross-section (<50%)"
        print(f"[s04] E4 read: {verdict}")

if __name__ == "__main__":
    main()
