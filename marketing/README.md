# Marketing corpus — "Lawyered vs. Loud" (venue divergence + AI-washing exposure)

Runs on the **same frozen random-400** as Paper A, reusing the shared frame, brochures, keys,
and prompts. Goal: collect each firm's **marketing** text, measure AI-washing **exposure**
(F1-F7 fingerprint) on marketing vs. brochures, and produce the **per-firm venue-divergence**
result. This is the empirical basis the split assessment found MISSING; running it decides
whether Paper 10 splits (SPLIT-DEFERRED → SPLIT) or folds B into A.

Shared inputs (read, never modified): `../data/pilot_sample_400.csv`,
`../data/brochure_text/current/`, `../pilot/prompts/*`, `../pilot/labels_primary.csv`,
`../build/common.py`. All B outputs stay in `marketing/`.

## Setup
```
cd "NIW/Paper 10/marketing"
source ../build/.venv/bin/activate      # reuse Paper A's venv
pip install -r requirements.txt
```

## Run order
| Step | Script | Does | Feeds |
|---|---|---|---|
| 1 | `b01_resolve_sites.py` | Extract each firm's website from its brochure cover text | B1 coverage |
| 2 | `b02_crawl_marketing.py` | Polite crawl of homepage + key pages; extract marketing text | B1 coverage |
| 3 | `b03_classify_marketing.py` | Typology + F1-F7 exposure on marketing; F1-F7 exposure on brochures (full scale) | B2 |
| 4 | `b04_divergence.py` | Per-firm venue divergence + bootstrap CI; writes `DIVERGENCE.md` | B1/B2 verdict |

```
python b01_resolve_sites.py
python b02_crawl_marketing.py
python b03_classify_marketing.py
python b04_divergence.py
```

## What each result decides (from splitcheck/SPLIT_VERDICT.md)
- **B1** — usable marketing text for **≥300** firms. b01/b02 print the coverage; if `<300`,
  top up `data/sites_manual.csv` (rows: `crd,url`) and rerun b02, or accept SPLIT-DEFERRED.
- **B2** — marketing exposure materially **> brochure exposure**, paired **95% CI excludes zero**
  (b04 prints this and the per-firm 2×2). Plus the venue-divergence rate.

If **b04 shows B1 PASS and B2 PASS**, tell me and I'll re-run the split check — it flips to
**SPLIT** and I write `BOUNDARY.md` (table/figure allocation, shared-method paragraph, word
budgets, sequencing, and the legal-care/reverse-identification check). If coverage or CI falls
short, B folds into Paper A as one "venue divergence" section (the SINGLE outcome).

## Notes
- Classifier defaults to `gpt-4o` (matches Paper A's final labels); override with `MODEL=…`.
  Hard `$30` budget guard (`BUDGET=…`), same $-tracking as A. Marketing pages are short, so
  cost is small.
- Crawling is best-effort and polite (1 req/s per host, ≤6 pages/firm, main-text extraction).
  Small advisers with thin/no sites will miss — that's the expected coverage risk, reported at
  each step. This measures **current** marketing vs current brochures (historical marketing is
  out of scope for the MVP).
- Legal-care: all B outputs are **aggregate** (shares, CIs, 2×2 counts). `venue_divergence.csv`
  is firm-level intermediate data — do NOT publish it or any per-firm exposure flag; the
  manuscript reports only aggregates, framed as similarity-screening, never misconduct. The
  legal-care check is formalized in BOUNDARY.md if the verdict flips to SPLIT.
