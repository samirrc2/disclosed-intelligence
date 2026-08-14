# Claim Typology — classification rubric v1 (frozen)

Implements P10.yaml design commitment #2 exactly. **Multi-label**: a brochure-year may carry
zero, one, or several labels. Labels are assigned on the basis of the brochure's own text about
the FILING FIRM's practices (not generic market commentary, not third-party managers the firm
merely allocates to unless the firm adopts the technology itself).

Scope of "AI" for this typology: artificial intelligence, machine learning, deep/neural
learning, generative AI / large language models, natural language processing, predictive
analytics/models, algorithmic or quantitative model-driven decisioning, and "data science"
when used as an investing/operations capability. Plain automation (e-signature, a CRM, a
portfolio-rebalancing rule) is NOT AI unless the text frames it as AI/ML/predictive.

## Labels
- **a — AI in investment process.** The firm states it uses AI/ML/predictive/algorithmic
  models in research, security selection, portfolio construction, signal generation, risk
  modeling for investing, or trading decisions.
- **b — AI in operations / client service.** The firm states it uses AI/ML in non-investment
  functions: client servicing, chatbots/virtual assistants, marketing, compliance/surveillance,
  document processing, back-office, cybersecurity, meeting notes, etc.
- **c — AI as a disclosed risk factor.** The brochure discusses AI/ML/algorithmic/model use as
  a source of RISK (e.g., model/AI risk disclosure, limitations of algorithms, reliance-on-
  technology risk, third-party AI risk, cybersecurity-from-AI risk).
- **d — Explicit prohibition / non-use.** The firm affirmatively states it does NOT use AI/ML,
  or restricts/prohibits its use (e.g., "we do not use artificial intelligence to manage client
  portfolios," staff prohibited from entering client data into GenAI tools).
- **e — Vendor / product named.** The brochure names a specific AI product, model, or vendor
  (e.g., ChatGPT/OpenAI, Google Gemini, a named quant/AI platform or data vendor used for its
  AI capability). Naming a generic custodian or CRM is NOT label e unless it is invoked as an
  AI capability.

## Derived flags (computed downstream, not labeled by the rater)
- **any_use = (a OR b OR e)** — "discloses ANY use of AI." Used for the wedge (E2).
- **mentions_ai = (a OR b OR c OR d OR e)** — any AI mention at all.

## Output contract (per brochure-year)
Return strict JSON:
```
{
  "crd": <int>,
  "firm": "<string>",
  "brochure_date": "<string or 'unknown'>",
  "a": 0|1, "b": 0|1, "c": 0|1, "d": 0|1, "e": 0|1,
  "evidence": {
     "a": "<shortest verbatim quote or ''>",
     "b": "<verbatim or ''>",
     "c": "<verbatim or ''>",
     "d": "<verbatim or ''>",
     "e": "<verbatim or ''>"
  },
  "notes": "<=200 chars; edge-case reasoning if any>"
}
```
Rules: a label is 1 **only** if supported by a verbatim quote placed in `evidence`. No quote →
label is 0. Absence of any AI content → all labels 0, evidence all "", note
"no AI/tech content". Do not infer AI from the mere existence of a website or software.
