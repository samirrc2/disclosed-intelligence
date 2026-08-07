# Run sequence

## Reproduce the article (offline — this capsule)

No keys, no network, no cost. From the repository root (or `/code/run` on Code Ocean):

```bash
bash reproduce.sh              # analyze frozen data + byte-identical replication check
bash reproduce.sh --analyze-only
bash reproduce.sh --test       # unit tests only
```

Outputs:

- Local: `results/latest/` — `metrics_summary.md`, `tables/`, `figures/`,
  `replication_check.md`
- Code Ocean: `/results/metrics_summary.md`, `/results/tables/`, `/results/figures/`,
  and `/results/latest/replication_check.md` (SHA-256 determinism check; expect **PASS**)

## Upstream collection (documented, NOT run here)

The frozen `data/` files were produced once by the collection pipeline. These steps
require network access and API keys and are recorded for transparency only
(details in `DATA_PROVENANCE.md`):

```
s01_frame.py          # parse SEC Form ADV Part 1 bulk data -> sampling frame
s02_sample.py         # stratified random sample of 400 firms (frozen)
s03_current_brochures.py   # retrieve current Part 2A brochure per firm from IAPD
s05_classify.py       # classify each brochure with gpt-4o (rubric v1); gpt-4o-mini on a 60-subsample
                      # independent cross-family re-coding of the 180 validation brochures
b01_resolve_sites.py … b04_divergence.py   # marketing crawl, classify, venue divergence
```

## Determinism

`analyze.py` reads only the frozen files in `data/` and uses no randomness. Running
it twice yields byte-identical tables; `replication_check.py` asserts this and writes
`results/latest/replication_check.md`.
