# AI-washing exposure fingerprint — v1 (frozen)

Extracted VERBATIM from the two SEC settled orders (the charged conduct). Sources:
- In re Delphia (USA) Inc., IA Rel. 6573 (Mar 18, 2024) — https://www.sec.gov/files/litigation/admin/2024/ia-6573.pdf
- In re Global Predictions Inc., IA Rel. 6574 (Mar 18, 2024) — https://www.sec.gov/files/litigation/admin/2024/ia-6574.pdf

## Charged claims (verbatim excerpts)
Delphia:
- "put[s] collective data to work to make our artificial intelligence smarter"
- "Delphia uses machine learning to analyze the collective data"
- client data used in "a predictive algorithmic model"
- "turns your data into an unfair investing advantage"
- "algorithms combine the data invested by its members ... to make predictions across thousands
   of publicly traded companies up to two years into the future"
- "the first investment adviser to convert personal data into a renewable source of investable capital"

Global Predictions:
- "[e]xpert AI-driven forecasts"
- "first regulated AI financial advisor"
- marketing AI capabilities the platform did not actually have (chatbot "does not generate
  allocation recommendations")

## Fingerprint patterns (F1–F7) — the screening instrument
A live brochure is flagged **exposed** if it makes a claim materially similar to any pattern.
This is a SCREENING measure, never an accusation. Similarity is judged on the claim's substance,
not exact wording.

- **F1 Predictive-power claim:** AI/ML/algorithms *predict/forecast* which securities, companies,
  or trends will outperform ("AI-driven forecasts", "predicts winners").
- **F2 First-mover / identity claim:** superlative self-identification as an AI adviser
  ("first/only AI financial advisor", "the AI-powered adviser").
- **F3 Edge/advantage claim:** proprietary AI/ML delivers an *investing edge, alpha, or
  advantage* over others ("unfair advantage", "smarter AI", "edge from machine learning").
- **F4 AI-manages-portfolios claim:** AI/ML *makes* allocation/trading/management decisions for
  client portfolios (vs. assisting humans).
- **F5 Learns-from-data claim:** AI/ML *learns/improves* from client or collective data to drive
  investment decisions.
- **F6 Quantified-capability claim:** specific quantified AI capability (predictions across
  thousands of companies, stated accuracy/horizon) presented as fact.
- **F7 Core-differentiator marketing:** "AI-driven"/"machine-learning-powered" used as the
  headline differentiator of the advisory *service* (not a hedged risk mention).

## Method for E3 (pilot-grade, flagged as such)
For each brochure with any AI content, the rater marks which of F1–F7 (if any) the text matches,
with a verbatim quote. A brochure is "exposed" if ≥1 fingerprint matches. Reported as the share
of pilot brochures exposed. This is *lexical/semantic-similarity screening by an LLM rater*, not
an embedding-threshold method; the full build will pre-register an embedding cosine threshold.
Mentions that are purely hedged risk-factor language (label c only, no promotional claim) are
NOT exposure.
