"""
s01_frame.py — obtain the Form ADV Part 1 structured data (the sampling frame).

What it does:
  1. Fetches SEC's "Form ADV Data" page and lists every downloadable data ZIP it finds
     (so you can confirm the current filenames — SEC renames these periodically).
  2. Downloads the target Part 1 structured ZIP (append-only, hashed) and unzips it.
  3. Prints the CSV tables inside and their column headers, so s02 can map columns.

Adjust FRAME_ZIP_URL below if SEC has posted a newer file (the page listing in step 1
will show you the current URL). The 2011->2024 Part 1 file is the documented default.

Usage:  python s01_frame.py
"""
import io, re, zipfile
from pathlib import Path
import requests
from common import sec_get, persist_raw, DATA, BUILD_OUT

FORM_ADV_DATA_PAGE = "https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data"
# Documented Part 1 structured data (Nov 2011 -> Dec 2024). Replace with a newer file if listed.
FRAME_ZIP_URL = "https://www.sec.gov/files/adv-filing-data-20111105-20241231-part1.zip"

FRAME_DIR = DATA / "frame"
FRAME_DIR.mkdir(parents=True, exist_ok=True)

def list_available_files():
    print(f"[s01] listing data files on {FORM_ADV_DATA_PAGE}")
    r = sec_get(FORM_ADV_DATA_PAGE)
    if r.status_code != 200:
        print(f"[s01]   could not fetch data page (HTTP {r.status_code}); skipping listing.")
        return
    links = sorted(set(re.findall(r'href="([^"]+\.zip)"', r.text)))
    for l in links:
        if l.startswith("/"):
            l = "https://www.sec.gov" + l
        print("   ", l)
    print(f"[s01] found {len(links)} .zip links (confirm FRAME_ZIP_URL against these).")

def download_frame():
    print(f"[s01] downloading frame ZIP: {FRAME_ZIP_URL}")
    r = sec_get(FRAME_ZIP_URL, stream=True, timeout=600)
    if r.status_code != 200:
        raise SystemExit(f"[s01] download failed HTTP {r.status_code}. "
                         f"Check FRAME_ZIP_URL against the listing above.")
    content = r.content
    z = persist_raw("frame", Path(FRAME_ZIP_URL).name, content, FRAME_ZIP_URL)
    print(f"[s01] saved {z}  ({len(content)/1e6:.1f} MB)")
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        names = zf.namelist()
        print(f"[s01] ZIP contains {len(names)} entries:")
        for n in names:
            print("     ", n)
        # extract CSVs and show headers
        for n in names:
            if n.lower().endswith((".csv", ".txt")):
                zf.extract(n, FRAME_DIR)
                p = FRAME_DIR / n
                with open(p, "r", encoding="latin-1", errors="replace") as fh:
                    header = fh.readline().strip()
                cols = header.split(",")
                print(f"\n[s01] {n}: {len(cols)} columns")
                print("      first cols:", cols[:25])
    print(f"\n[s01] extracted to {FRAME_DIR}")
    print("[s01] NEXT: run s02_sample.py (it auto-detects CRD / AUM / private-fund columns).")

if __name__ == "__main__":
    list_available_files()
    download_frame()
