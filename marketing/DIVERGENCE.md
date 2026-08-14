# P10B_DIVERGENCE — venue divergence result (auto-generated)

Firms with BOTH brochure and marketing classified: **283**

## Exposure (AI-washing fingerprint F1-F7)
- Brochure ("lawyered"): **0.7%** exposed
- Marketing ("loud"):    **0.7%** exposed
- Paired gap (marketing - brochure): **+0.000**  95% CI [-0.014, +0.014]
- CI excludes zero: **False**  <- this is criterion B2

## Per-firm 2x2 (exposure)
| | brochure exposed | brochure clean |
|---|---|---|
| marketing exposed | 0 | 2 |
| marketing clean | 2 | 279 |

Venue-divergence rate (disagree across venues): **4/283 = 1.4%**

## Read for the split gate
- B1 (coverage >=300 firms both venues): **FAIL** (n=283)
- B2 (marketing exposure materially > brochure, CI excludes 0): **FAIL**
If both PASS, re-run splitcheck -> verdict flips to SPLIT and BOUNDARY.md is written.
