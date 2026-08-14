# Disclosed Intelligence

Computational artifact and manuscript for the *Frontiers in Artificial Intelligence* article:

**Disclosed Intelligence: A Large-Sample Measurement of AI Disclosure in U.S. Investment Adviser Fiduciary Filings**

### Paper summary

We measure how U.S. registered investment advisers disclose their use of artificial
intelligence in the fiduciary documents clients actually receive — Form ADV Part 2A
brochures. Over a stratified sample of advisers (388 brochures classified against a
frozen five-label typology), we quantify how much AI use is disclosed, in what framing,
how it varies with adviser type and size, and how brochure disclosure compares with the
same firms' public website marketing. Classifier reliability is established with an
independent, cross-model-family re-coding, weighted to the population via a two-phase
verification sample.

**Main findings:**

- **Disclosed any-use is 23.7%** (95% CI 19.7–28.2; n=388). Survey-weighted to the
  brochure-filing universe it is 22.7%.
- **The dominant framing is risk, not capability:** 27.6% of brochures disclose AI as a
  *risk factor*, while explicit claims of use in the investment process are rarer.
- **Disclosure rises strongly with adviser size and differs by type** (private-fund vs.
  wealth/retail): a monotone AUM gradient, significant in both a trend test and a logistic model.
- **The classifier is reliable:** design-weighted independent cross-family validation gives
  any-use κ=0.738 (precision 0.761, recall 0.837); the risk-factor label is almost-perfect (κ=0.934).
- **AI-washing exposure is rare:** 5/388 brochures (1.3%) match charged-conduct language
  distilled from SEC enforcement orders IA-6573/IA-6574.
- **The brochure is the more AI-forward venue:** across 283 firms observed in both venues,
  disclosed any-use is 23.0% in brochures vs. 5.7% in website marketing.

This repository is the frozen dataset, the deterministic analysis pipeline that regenerates
those results, and the Frontiers manuscript package.

---

## 1. Artifact identification

| Field | Value |
|-------|-------|
| **Article title** | Disclosed Intelligence: A Large-Sample Measurement of AI Disclosure in U.S. Investment Adviser Fiduciary Filings |
| **Authors** | Samir Chincholikar, Robin Chawla |
| **Affiliations** | Independent Researcher, New York, NY, United States; Independent Researcher, New York, NY, United States |
| **Code repository** | https://github.com/samirrc2/disclosed-intelligence |
| **Persistent DOI** | https://doi.org/10.24433/CO.3404788.v1 (`10.24433/CO.3404788.v1`) |
| **Contact** | Samir Chincholikar: samir.chincholikar@gmail.com; Robin Chawla: robin.chawla.cse14@iitbhu.ac.in |
| **ORCID** | Samir Chincholikar: 0009-0007-2779-3492; Robin Chawla: 0009-0007-2807-3948 |

The artifact enables independent reproduction of the article's computational results
from a frozen, pseudonymized dataset. That path requires **no API keys** and incurs
**no inference cost**. Re-collecting the raw SEC filings and running the LLM classifier
is optional and **not required** to verify any number in the article.

---

## 2. Repository layout

```
manuscript/     The paper. latex/ = compilable source (manuscript.tex + figures + class/style);
                manuscript.pdf = compiled; supplements/ = S1, S2, coding kit; cover letter + compliance.
capsule/        The Code Ocean reproducibility capsule (self-contained). code/ + frozen data/ +
                docs/ + environment/ + results/. Run:  cd capsule && bash reproduce.sh
analysis/       Design-based inference: weighting, trend/logit, missingness, coding-sheet build.
build/          Live collection: Form ADV frame, sampling, brochure retrieval, classification.
marketing/      Venue comparison: resolve firm websites, crawl, classify, brochure-vs-marketing divergence.
data/ pilot/    Working sample, labels, prompts, and the pilot that gated the study.
recon/          Phase-0 data-availability reconnaissance.
run_all.sh      Live end-to-end pipeline (needs keys). requirements.txt = dependencies.
DATA_AVAILABILITY.md · CITATION.cff · .zenodo.json · LICENSE · DECISIONS.md
```

## 3. Reproduce the published results (offline, no keys)

```
cd capsule
bash reproduce.sh          # analyze frozen data + byte-identical determinism check
```

Outputs land in `capsule/results/`: `metrics_summary.md` (verdict first), `tables/*.csv`,
and `figures/*.{png,svg}`. See `capsule/AUDIT.md` for the last full verification run.

## 4. Re-collect from source (optional, needs API keys)

```
./run_all.sh               # build -> analysis -> marketing; keys from ../API Keys/keys.env.txt
```

## The final manuscript

`manuscript/manuscript.pdf` (source: `manuscript/latex/manuscript.tex`). Upload instructions
for Frontiers are in `manuscript/SUBMISSION_README.md`.
