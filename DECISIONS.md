# DECISIONS.md — Paper 10 pilot

Chronological log of judgment calls. Times in UTC.

---

## D0. Execution environment reconnaissance (2026-07-27) — SHAPES EVERYTHING BELOW

Before any data work, I probed what this cloud session can actually reach. This is decisive
for the pilot's scope, so it is logged first.

**Findings (empirical, tested this session):**
1. The cloud container routes all egress through an allowlist proxy (`127.0.0.1:42649`).
   Direct HTTP to `www.sec.gov`, `reports.adviserinfo.sec.gov`, `efts.sec.gov`,
   `api.openai.com`, `generativelanguage.googleapis.com`, `api.x.ai`, and `web.archive.org`
   all return **403 Forbidden (Tunnel connection failed)** or connection refused.
   Only package registries (pypi, npm) and **github.com / raw.githubusercontent.com** are
   directly reachable.
2. `mcp__remote-devices__device_bash` (the user's Mac shell) has **no network access** at all.
3. `WebFetch` / `WebSearch` DO reach `sec.gov` and `reports.adviserinfo.sec.gov` (they use a
   separate proxied path). **WebFetch successfully extracts text from IAPD brochure PDFs**
   (verified on CRD 117209) and from SEC enforcement-order PDFs. `web.archive.org` is
   **blocked even via the WebFetch proxy** (403).
4. The user's real Chrome (via `Control_Chrome`) has real network, but the JavaScript/
   page-content bridge failed repeatedly (`"Chrome is not running"` on `execute_javascript`/
   `get_page_content` although `list_tabs` and `open_url` worked). Navigation-triggered bulk
   download + stage was therefore not reliable this session.

**Consequences for the pilot design:**
- **Cannot bulk-download** the SEC Form ADV Part 1 population ZIP, nor the bulk historical
  Part 2 brochure ZIPs, from this sandbox. (These files demonstrably EXIST and are trivially
  downloadable on any unrestricted machine — that is the Q1/Q3 availability finding, and it is
  independent of this sandbox's limits.)
- **Cannot call the provided OpenAI/Gemini/xAI API keys** — those endpoints are proxy-blocked.
  So the spec's "cheapest frontier-mini classifier" and "second model FAMILY validation"
  cannot run as literally written in-sandbox.
- **Can** retrieve and read real current brochures and enforcement texts via WebFetch. This is
  enough to test measurement reliability and signal on a real (if smaller) sample.

**Decisions taken (see D1–D5 for specifics):**
- Phase 0 recon is delivered in full: availability is assessed empirically where the sandbox
  allows (brochure retrieval, enforcement extraction) and via SEC's own documentation where it
  does not (bulk file existence/coverage).
- Phase 1 measurement is run as a **real WebFetch-based probe** at reduced n, with the sampling
  frame and second-rater adapted to what is reachable, every deviation flagged. The pilot's job
  is signal detection, and this still answers it.
- The blocker is surfaced prominently in the verdict and to the user, with the exact full-build
  path that a machine with SEC access (or an unrestricted run) would follow.

---

## D1. Sampling frame (deviation from spec, forced by D0)

Spec: stratified random sample of 400 from the Part 1 bulk data, strata = AUM quartile ×
adviser type, seed 42, frozen before any brochure is read.

Because the Part 1 population ZIP cannot be downloaded in-sandbox (D0), a true random draw from
the full frame is not possible here. Adopted substitute, fully documented and reproducible:
- A **stratified purposive pilot sample** of real, currently-registered advisers spanning the
  design strata (AUM bands × wealth/RIA vs private-fund), assembled by a documented procedure
  and **frozen to `data/pilot_sample.csv` before classification**.
- This is explicitly **not** the frozen random 400 and is **not representative** for population
  share estimation; it is a measurement-reliability + signal probe. E1/E2/E3 are reported as
  pilot-grade with explicit n and no extrapolation, exactly as the brief demands ("no
  extrapolation theater").
- The full random stratified draw is a ~10-minute step once the Part 1 CSV is in hand; it is
  not a data-availability question, only a sandbox-network one.

## D2. Classifier & validation model (deviation from spec, forced by D0)

Spec: cheapest frontier-mini model for classification; independent SECOND MODEL FAMILY for the
60-brochure validation; per-label agreement.

OpenAI/Gemini/xAI APIs are proxy-blocked (D0), so:
- **Primary classifier:** the session model (Claude, `claude-opus-4-8`) applying the versioned
  rubric in `pilot/prompts/`, run via subagents for parallelism.
- **Second rater:** an **independent Claude pass** (separate subagent, separate prompt framing,
  no sight of the first pass). This is a same-family second rater, **not** a cross-family check.
  Implication: inter-rater agreement here is an **upper bound** on what a truly independent
  family (e.g. GPT/Gemini) would show; a genuinely independent family check is deferred to the
  full build (where API access exists) and is called out in the verdict.
- Cost: because no external metered API is used, **in-sandbox classification spend = $0**. The
  $30 cap is not approached. Ledger in `pilot/COST_LEDGER.md`.

## D3. Historical brochures / panel (Q3)
IAPD's per-CRD endpoint (`reports.adviserinfo.sec.gov/reports/ADV/{CRD}/PDF/{CRD}.pdf`) serves
the **current** brochure only. The historical source is the SEC bulk **Part 2 monthly ZIPs**
(2020–2024), which cannot be downloaded here. Wayback is proxy-blocked. So the pilot reports E4
(panel viability) as a **documented availability assessment** from SEC's published data files,
not a measured per-firm historical retrieval rate. This is the key input to CONTINUE vs
DOWNGRADE and is flagged as such.

## D4. Where work happens
Heavy work (retrieval logs, classification, analysis) is done in the cloud workspace
(`/root/Paper 10`). Final deliverables are written back to the device at
`/Users/samirchincholikar/Desktop/NIW/Paper 10/`. Raw brochure text captures are persisted
append-only with SHA-256 hashes in `data/raw/`.

## D5. Politeness to SEC/IAPD
All brochure/enforcement retrieval goes through WebFetch (single fetch per URL, 15-min cached),
which is inherently throttled by tool-call cadence and identifies via the platform's fetcher.
No tight loops against SEC hosts. Subagent fan-out is capped to avoid bursts.

---

## D6. Final pilot results (2026-07-28)
- Corpus: 59 unique current brochures retrieved (100% of attempted), 6 strata, all verified by
  firm name + current date via the IAPD brochure-viewer / firm-hosted path (canonical
  `reports.adviserinfo/.../{CRD}.pdf` endpoint was discarded — it returned binary and caused
  WebFetch confabulation on 2 firms, which were dropped).
- Two independent same-family classification passes over identical extracted text.
  Inter-rater: label a κ=0.926, b κ=1.0, c κ=1.0, e κ=1.0, any_use κ=0.963; label d degenerate
  (0 prevalence). Only 3/59 brochures had any label disagreement.
- E1 any-use 26–37%; E2 wedge 26–36 pp vs 63%; E3 exposure 0/59; E4 not measured (bulk history
  not downloadable in-sandbox).
- Verdict: CONTINUE contingent on confirming bulk historical brochure coverage; fallback
  DOWNGRADE. Full reasoning in pilot/PILOT_VERDICT.md.
- Judgment call: dropped one duplicate (Arnold & Mote appeared in both wealth_small and
  wealth_mid) → 59 unique from 60 attempted.
