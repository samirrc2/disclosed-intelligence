"""
b04_divergence.py — the Paper B headline: per-firm venue divergence + aggregate exposure gap.

Compares each firm's AI posture in its LAWYERED brochure vs its LOUD marketing:
  - any-use claims: brochure (Paper A labels) vs marketing (b03)
  - AI-washing exposure (F1-F7): brochure (b03 full-scale) vs marketing (b03)
Reports the paired exposure gap with a bootstrap 95% CI (does it exclude zero? -> B2), the
per-firm 2x2 distribution, and the venue-divergence rate.

Inputs: marketing/out/{marketing_labels,marketing_exposure,brochure_exposure}.csv,
        ../pilot/labels_primary.csv (brochure typology from Paper A)
Outputs: marketing/out/venue_divergence.csv (per firm), marketing/DIVERGENCE.md, marketing/out/divergence_summary.json

Usage:  python b04_divergence.py
"""
import json, csv
import pandas as pd
from b_common import BOUT, BROOT, P10, bootstrap_ci

def load(path, idx="crd"):
    p = pd.read_csv(path); p[idx] = p[idx].astype(int)
    return p.set_index(idx)

def main():
    mlab = load(BOUT / "marketing_labels.csv")
    mexp = load(BOUT / "marketing_exposure.csv")
    bexp = load(BOUT / "brochure_exposure.csv")
    blab = load(P10 / "pilot" / "labels_primary.csv")

    mlab["m_anyuse"] = ((mlab[["a", "b", "e"]].sum(axis=1)) > 0).astype(int)
    blab["b_anyuse"] = ((blab[["a", "b", "e"]].sum(axis=1)) > 0).astype(int)

    firms = sorted(set(mexp.index) & set(bexp.index))   # firms with BOTH venues classified
    rows = []
    for crd in firms:
        b_use = int(blab.loc[crd, "b_anyuse"]) if crd in blab.index else None
        m_use = int(mlab.loc[crd, "m_anyuse"]) if crd in mlab.index else None
        b_exp = int(bexp.loc[crd, "exposed"]); m_exp = int(mexp.loc[crd, "exposed"])
        rows.append({"crd": crd, "b_anyuse": b_use, "m_anyuse": m_use,
                     "b_exposed": b_exp, "m_exposed": m_exp,
                     "exposure_gap": m_exp - b_exp,
                     "anyuse_gap": (m_use - b_use) if (b_use is not None and m_use is not None) else ""})
    with open(BOUT / "venue_divergence.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    n = len(firms)
    b_exp_share = sum(r["b_exposed"] for r in rows) / n
    m_exp_share = sum(r["m_exposed"] for r in rows) / n
    gap, lo, hi = bootstrap_ci([r["exposure_gap"] for r in rows])
    # 2x2 exposure
    cell = lambda mb: sum(1 for r in rows if (r["m_exposed"], r["b_exposed"]) == mb)
    both, mkt_only, bro_only, neither = cell((1, 1)), cell((1, 0)), cell((0, 1)), cell((0, 0))
    diverge = mkt_only + bro_only

    summ = {
        "n_firms_both_venues": n,
        "brochure_exposure_share": round(b_exp_share, 4),
        "marketing_exposure_share": round(m_exp_share, 4),
        "exposure_gap_mean": None if gap is None else round(gap, 4),
        "exposure_gap_CI95": [None if lo is None else round(lo, 4), None if hi is None else round(hi, 4)],
        "ci_excludes_zero": (lo is not None and (lo > 0 or hi < 0)),
        "exposure_2x2": {"both": both, "marketing_only": mkt_only, "brochure_only": bro_only, "neither": neither},
        "venue_divergence_rate": round(diverge / n, 4),
    }
    json.dump(summ, open(BOUT / "divergence_summary.json", "w"), indent=1)

    md = f"""# DIVERGENCE — venue divergence result (auto-generated)

Firms with BOTH brochure and marketing classified: **{n}**

## Exposure (AI-washing fingerprint F1-F7)
- Brochure ("lawyered"): **{b_exp_share:.1%}** exposed
- Marketing ("loud"):    **{m_exp_share:.1%}** exposed
- Paired gap (marketing - brochure): **{'' if gap is None else f'{gap:+.3f}'}**  95% CI [{'' if lo is None else f'{lo:+.3f}'}, {'' if hi is None else f'{hi:+.3f}'}]
- CI excludes zero: **{summ['ci_excludes_zero']}**  <- this is criterion B2

## Per-firm 2x2 (exposure)
| | brochure exposed | brochure clean |
|---|---|---|
| marketing exposed | {both} | {mkt_only} |
| marketing clean | {bro_only} | {neither} |

Venue-divergence rate (disagree across venues): **{diverge}/{n} = {diverge/n:.1%}**

## Read for the split gate
- B1 (coverage >=300 firms both venues): **{'PASS' if n >= 300 else 'FAIL'}** (n={n})
- B2 (marketing exposure materially > brochure, CI excludes 0): **{'PASS' if summ['ci_excludes_zero'] else 'FAIL'}**
If both PASS, re-run splitcheck -> verdict flips to SPLIT and BOUNDARY.md is written.
"""
    (BROOT / "DIVERGENCE.md").write_text(md)
    print(md)
    print(f"[b04] wrote marketing/DIVERGENCE.md, out/venue_divergence.csv, out/divergence_summary.json")

if __name__ == "__main__":
    main()
