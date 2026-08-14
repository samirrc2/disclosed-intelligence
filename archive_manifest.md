# Archive manifest — frozen data assets (the paper's inputs)

These files are the paper's **frozen, pseudonymized primary data**, held in the
audited Code Ocean capsule under `capsule/data/`. Do **not** regenerate them; any
correction requires a new versioned file plus a changelog entry here.

## Reproducibility model

The disclosure labels were produced by a large-language-model pass over Form ADV
Part 2A brochure text (network, cost, and model-version sensitive) plus an independent
cross-family re-coding. As with a frozen model-output dataset, that classification is
**not re-executed**; the label tables are frozen and the pipeline reproduces every
published number and figure from them 100% offline. Firm identifiers are pseudonymized;
the crosswalk to CRD identifiers is withheld.

## Key frozen assets (SHA-256)

| Asset | Role | SHA-256 |
|-------|------|---------|
| `capsule/data/sample.csv` | frozen input | `25712b741d28c3f45250437cd1aae96aa016a3ac6db6f8c8d4aadfb3d2e9c9e2` |
| `capsule/data/labels_primary.csv` | frozen input | `c1e1710c91070e7051dd2b3fe76df18e79324f434589097726e9aeb68ada0644` |
| `capsule/data/labels_independent.csv` | frozen input | `2f040dec825672eb8a3b5cc364bd576d684dde5ab50e3a550b1574373abc25ac` |
| `capsule/data/labels_secondary_sub.csv` | frozen input | `278031e05e079c0e707e0d986cc95d174c720050af987efb4424a1a10c06538f` |
| `capsule/data/population_strata.csv` | frozen input | `f9d85cd44efe093700a8681f9290741bbcda0f0193b46bd74d2d1e4fe0d0a985` |

Venue tables under `capsule/data/venue/` and instruments under `capsule/data/prompts/`
are part of the same frozen release; `bash reproduce.sh` verifies the full pipeline.

## Corrections log
- (none)
