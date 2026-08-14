# Reproducibility audit

Last full verification of this capsule (offline, no network, no API keys).

| Check | Result |
|---|---|
| Capsule integrity | SHA-256 of the packaged capsule matched byte-for-byte between disk and the verification run |
| Environment | Pinned deps installed from `code/requirements.txt` (numpy 2.2.6, pandas 2.2.3, scipy 1.14.1, statsmodels 0.14.4, matplotlib 3.9.2) |
| `bash reproduce.sh` | Completed, exit 0 |
| Determinism | Two independent runs produced **byte-identical** table artifacts — PASS |
| Unit tests | `6 passed` |
| Manuscript audit | **AUDIT PASS** — every headline number recomputes exactly from the frozen data |
| Figures | All four manuscript figures regenerate (typology, gradient, validation, venue) |
| Loop closure | Each audited value (N=388; any-use 23.7% [19.7–28.2]; any-mention 31.7%; risk-factor 27.6%; precision 0.761; recall 0.837; κ=0.738; validation n=180) is present in `../manuscript/latex/manuscript.tex` |

Reproduce it yourself:  `bash reproduce.sh`  (from this `capsule/` directory).
