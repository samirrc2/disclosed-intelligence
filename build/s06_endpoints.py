"""
s06_endpoints.py — compute E1-E4 on the full sample and apply the verdict gate.

E1 typology distribution (population-weighted by strata if sample is proportional).
E2 wedge = 63% (Schwab 2026, cited) - any-use disclosure share.
E3 exposure = run the fingerprint pass separately (pilot used an LLM screen; the build should
   pre-register an embedding-cosine threshold vs the enforcement-order claim vectors).
E4 = per-year panel coverage from s04.

Usage:  python s06_endpoints.py
"""
import json, csv
import pandas as pd
from pathlib import Path
from common import ROOT, DATA, BUILD_OUT

LAB = ROOT / "pilot" / "labels_primary.csv"
SAMPLE = DATA / "pilot_sample_400.csv"
PANEL = BUILD_OUT / "panel_coverage.csv"
SCHWAB = 0.63

def main():
    lab = pd.read_csv(LAB)
    smp = pd.read_csv(SAMPLE)
    df = smp.merge(lab, on="crd", how="inner")
    n = len(df)
    df["any_use"] = ((df["a"] | df["b"] | df["e"]) > 0).astype(int)
    df["mentions"] = ((df[["a","b","c","d","e"]].sum(axis=1)) > 0).astype(int)

    print(f"=== E1 typology (n={n}) ===")
    for L in ["a","b","c","d","e"]:
        print(f"  {L}: {df[L].sum()}/{n} = {df[L].mean():.1%}")
    print(f"  any_use(a|b|e): {df['any_use'].sum()}/{n} = {df['any_use'].mean():.1%}")
    print(f"  any mention:    {df['mentions'].sum()}/{n} = {df['mentions'].mean():.1%}")

    # by stratum (for representative weighting)
    print("\n  any_use by stratum:")
    g = df.groupby(["type","aum_quartile"])["any_use"].agg(["mean","size"])
    print(g)

    print("\n=== E2 wedge ===")
    au = df["any_use"].mean()
    print(f"  disclosure any-use share = {au:.1%}")
    print(f"  wedge vs Schwab 63%      = {(SCHWAB-au)*100:.1f} pp")

    print("\n=== E4 panel viability ===")
    if PANEL.exists():
        p = pd.read_csv(PANEL); print(p.to_string(index=False))
        early = p[(p["year"] <= 2023)]["coverage"].dropna()
        if len(early):
            print("  E4 read:", "PANEL" if early.min() >= 0.5 else "DOWNGRADE (cross-section)")
    else:
        print("  run s04_panel_brochures.py to populate E4.")

    out = {"n": n, "E1": {L: int(df[L].sum()) for L in list("abcde")},
           "any_use_share": float(au), "wedge_pp": float((SCHWAB-au)*100)}
    json.dump(out, open(BUILD_OUT / "endpoints_full.json", "w"), indent=1)
    print(f"\nsaved {BUILD_OUT/'endpoints_full.json'}")

if __name__ == "__main__":
    main()
