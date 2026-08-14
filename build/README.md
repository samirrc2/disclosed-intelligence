# build/ — local pipeline to clear the pilot blockers

Everything here runs on **your Mac** (which has network + your API keys), not the sandbox.
It solves the blockers from the issues table: bulk SEC download, the real stratified-400 draw,
full-PDF brochure retrieval, historical panel confirmation, and real cross-family classification.

## Setup
```bash
cd "NIW/Paper 10/build"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python common.py            # sanity check: prints how many keys loaded per provider + User-Agent
```
Keys are read automatically from `../../API Keys/keys.env.txt` (the file you already have).
Set your identity once — edit `USER_AGENT` in `common.py` if you want a different contact string
(SEC fair-access requires a real contact; it defaults to your name + email).

## Run order
| Step | Script | What it does | Solves |
|---|---|---|---|
| 1 | `s01_frame.py` | Lists SEC data files, downloads Part 1 structured ZIP, prints table schema | bulk-download blocker, Q1 |
| 2 | `s02_sample.py` | Auto-detects CRD/AUM/private-fund cols, draws **stratified random 400** (seed 42), freezes `data/pilot_sample_400.csv` | true random sample, AUM-band accuracy |
| 3 | `s03_current_brochures.py` | Pulls each firm's current brochure PDF (direct endpoint; API+viewer fallback), full-text via pdfplumber, raw persisted+hashed | brochure retrieval, extraction recall |
| 4 | `s04_panel_brochures.py` | Downloads SEC bulk Part 2 monthly ZIPs, reports **per-year coverage** → PANEL vs DOWNGRADE | E4 / the paper's shape |
| 5 | `s05_classify.py` | Real **OpenAI-mini** classification + **cross-family** (xAI/Gemini) validation on 60, kappa, **$30 abort** | same-family limitation, budget test |
| 6 | `s06_endpoints.py` | E1/E2/E4 on the full sample, wedge vs 63%, verdict gate | population estimates |

```bash
python s01_frame.py && python s02_sample.py && python s03_current_brochures.py
python s04_panel_brochures.py
python s05_classify.py && python s06_endpoints.py
```

## The 3 spots most likely to need a one-line tweak (all print what they see)
1. **s01/s02 column names.** SEC's structured columns are coded (`5F2c`, `1E1`, …). s01 prints
   every header; if s02's auto-detect picks wrong, set `CRD_COL/AUM_COL/PF_COL` at the top of s02.
2. **s04 Part 2 ZIP internals.** The bulk brochure ZIPs are large and their layout has changed
   over years. s04 downloads + prints the structure and tries two mapping strategies; if neither
   fires, the printout shows you the index/filename pattern to map (usually a one-liner).
3. **s05 model names.** Defaults: primary `gpt-4o-mini`, secondary `grok-2-latest`. Override via
   `PRIMARY_MODEL` / `SECONDARY_MODEL` env vars (e.g. `PRIMARY_MODEL=gpt-5-mini`). Confirm your
   Gemini keys are standard `AIza…` Generative-Language keys if you switch the secondary to Gemini
   — the ones in keys.env.txt are an unusual `AQ.…` format and may be OAuth tokens, not API keys.

## Guarantees kept
- Raw downloads are **append-only** with SHA-256 in `data/raw/MANIFEST.csv` (never overwritten).
- SEC/IAPD hit with an identified User-Agent, **≥1.1 s between requests per host**, backoff on 429/5xx.
- Classification aborts hard at **$30**; the live ledger is in `pilot/validation_agreement.json`.
- The 400 sample is frozen to disk **before** any brochure is read (design commitment #1).

## What this does NOT do
It does not draft the paper. It reproduces and scales the pilot's measurement so you can confirm
the verdict on real, representative data, then hand off to the full-build prompt.
