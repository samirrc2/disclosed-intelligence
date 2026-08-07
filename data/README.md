# Data (`/data` mount)

All files are **frozen intermediate artifacts**. The expensive, networked upstream
steps — downloading SEC Form ADV bulk data, retrieving each brochure from IAPD, and
classifying brochures with a large language model — are **not** re-run here. Their
outputs are frozen so the statistical results reproduce deterministically and for free.

## Privacy / pseudonymization

Per the article's Data Availability statement, firm-level classifications are **not**
released against identifiable firms. Every record here is keyed by a pseudonymous
`fid` (`F0001`…`F0400`); firm names and CRD numbers are withheld. The analysis is
invariant to firm identity, so all published statistics reproduce exactly. The CRD
crosswalk is retained privately by the authors and available on request under the
terms described in the article; it is required only to re-fetch raw brochures, not to
reproduce any result.

## Files

| File | Rows | Contents |
|---|---|---|
| `sample.csv` | 400 | Frozen stratified random sample: `fid, type, aum_quartile, regulatory_aum`. |
| `labels_primary.csv` | 388 | Primary classifier (OpenAI gpt-4o) typology labels `a,b,c,d,e` per classified brochure. |
| `labels_secondary_sub.csv` | 60 | Same-family second rater (gpt-4o-mini) on a random 60-brochure subsample (reproducibility check). |
| `labels_independent.csv` | 180 | Independent, blinded re-coding by a different model family (validation reference). |
| `population_strata.csv` | 8 | Population count `N_all` per (type × AUM quartile) stratum, derived once from the SEC Form ADV Part 1 frame (see below). |
| `venue/venue_divergence.csv` | 283 | Firms with both a classified brochure and usable marketing text: per-venue any-use and exposure flags. |
| `venue/brochure_exposure.csv` | 388 | AI-washing exposure screen (F1–F7) applied to brochures. |
| `venue/marketing_exposure.csv` | 283 | Exposure screen applied to marketing text. |
| `venue/marketing_labels.csv` | 283 | Typology labels applied to marketing text. |
| `venue/marketing_crawl_log.csv` | 400 | Marketing-text retrieval status and character counts (for the selection analysis). |
| `venue/divergence_summary.json` | — | Precomputed venue summary (reference; recomputed by the code). |
| `prompts/typology_v1.md` | — | Frozen five-label classification rubric (the measurement instrument). |
| `prompts/exposure_fingerprints_v1.md` | — | Frozen F1–F7 exposure-language fingerprint, distilled from SEC orders IA-6573/IA-6574. |

## Provenance of `population_strata.csv`

The eight stratum population counts are the only artifact derived from the full
4.4 GB SEC Form ADV bulk dataset, which is public but too large (and firm-identifiable)
to redistribute here. They were computed once from `IA_ADV_Base_A` by replicating the
sampling frame exactly: parse CRD (`1E1`), regulatory AUM (`5F2c`), private-fund flag
(`7B`), and `DateSubmitted`; keep the latest filing per CRD; restrict to 2024+ filings
reporting non-negative AUM (N = 16,223 advisers); assign AUM quartiles by rank; and
count firms per (type × quartile). The bulk source is the SEC's public *Investment
Adviser Report – ADV bulk data* download.

## Reproduce

```bash
bash reproduce.sh              # analyze + byte-identical replication check
bash reproduce.sh --analyze-only
bash reproduce.sh --test
```

Outputs land in `results/latest/` (local) or `/results` (Code Ocean).
