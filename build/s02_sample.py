"""
s02_sample.py — draw the frozen stratified random sample of 400 (seed 42).

Corrected for the real SEC IA structured schema (IA_ADV_Base_A_*.csv):
    CRD           = column '1E1'     (5-6 digit FINRA CRD; '1D' is the 801- SEC file number)
    total RAUM    = column '5F2c'    (Item 5.F.(2)(c); 5F2a/b are discretionary/non-discretionary)
    private fund  = column '7B'      (Item 7.B "adviser to any private fund?", 'Y'/'N')
    firm name     = column '1A'
The file spans 2011->2024 (many filings per firm), so we keep each firm's LATEST filing and
restrict to firms active through MIN_LATEST_YEAR (a currently-registered proxy).

Strata = AUM quartile (4) x type (private-fund vs wealth/RIA) = 8 cells, 50 each = 400.
FROZEN to data/pilot_sample_400.csv BEFORE any brochure is read (design commitment #1).

Usage:  python s02_sample.py
"""
import glob
import pandas as pd
from pathlib import Path
from common import DATA

FRAME_DIR = DATA / "frame"
SEED = 42
PER_CELL = 50
MIN_LATEST_YEAR = 2024          # keep firms whose most-recent filing is >= this year
OUT = DATA / "pilot_sample_400.csv"

CRD_COL, AUM_COL, PF_COL, FIRM_COL, DATE_COL = "1E1", "5F2c", "7B", "1A", "DateSubmitted"

def _find_ia_base_a():
    cands = glob.glob(str(FRAME_DIR / "**" / "IA_ADV_Base_A*.csv"), recursive=True)
    if not cands:
        raise SystemExit("[s02] IA_ADV_Base_A_*.csv not found under data/frame — rerun s01_frame.py.")
    return sorted(cands, key=lambda p: Path(p).stat().st_size, reverse=True)[0]

def main():
    path = _find_ia_base_a()
    print(f"[s02] loading {path}")
    df = pd.read_csv(path, encoding="latin-1", low_memory=False, dtype=str)
    df.columns = [c.strip().strip('"') for c in df.columns]
    for col in (CRD_COL, AUM_COL, FIRM_COL):
        if col not in df.columns:
            raise SystemExit(f"[s02] expected column {col!r} missing; columns are: {list(df.columns)[:30]}")

    df["_crd"] = pd.to_numeric(df[CRD_COL], errors="coerce")
    df["_aum"] = pd.to_numeric(df[AUM_COL].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce")
    df["_dt"]  = pd.to_datetime(df.get(DATE_COL), errors="coerce")
    df = df.dropna(subset=["_crd"])

    # latest filing per firm
    df = df.sort_values("_dt").drop_duplicates("_crd", keep="last")
    before = len(df)
    if df["_dt"].notna().any():
        df = df[df["_dt"].dt.year >= MIN_LATEST_YEAR]
    print(f"[s02] firms: {before} unique -> {len(df)} active since {MIN_LATEST_YEAR}")

    df = df.dropna(subset=["_aum"])
    df = df[df["_aum"] >= 0]

    # type
    pf = df[PF_COL].astype(str).str.strip().str.upper() if PF_COL in df.columns else pd.Series("N", index=df.index)
    df["_type"] = pf.map(lambda x: "private_fund" if x == "Y" else "wealth_ria")

    # AUM quartiles within positive-AUM universe
    pos = df[df["_aum"] > 0].copy()
    pos["_q"] = pd.qcut(pos["_aum"].rank(method="first"), 4, labels=["Q1", "Q2", "Q3", "Q4"])
    df = df.merge(pos[["_crd", "_q"]], on="_crd", how="left")
    df["_q"] = df["_q"].astype("object").fillna("Q1")

    picks = []
    for t in ["private_fund", "wealth_ria"]:
        for q in ["Q1", "Q2", "Q3", "Q4"]:
            cell = df[(df["_type"] == t) & (df["_q"] == q)]
            take = min(PER_CELL, len(cell))
            if take < PER_CELL:
                print(f"[s02] cell {t}/{q}: only {len(cell)} available, taking {take}")
            if take:
                picks.append(cell.sample(n=take, random_state=SEED))
    sample = pd.concat(picks).reset_index(drop=True)

    out = sample[["_crd", "_type", "_q", "_aum"]].rename(
        columns={"_crd": "crd", "_type": "type", "_q": "aum_quartile", "_aum": "regulatory_aum"})
    out.insert(1, "firm", sample[FIRM_COL].values)
    out["crd"] = out["crd"].astype(int)
    out.to_csv(OUT, index=False)
    print(f"[s02] FROZEN {len(out)} firms -> {OUT}")
    print(out.groupby(["type", "aum_quartile"]).size())

if __name__ == "__main__":
    main()
