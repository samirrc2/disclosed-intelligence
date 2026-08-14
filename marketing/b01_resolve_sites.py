"""
b01_resolve_sites.py — resolve each sampled firm's marketing website.

Self-contained: extracts the firm's own domain from its Form ADV brochure cover text
(brochures reliably print the adviser's website), which we already have from Paper A's s03.
No search API needed. Firms whose brochure has no usable URL are marked missing (report the
coverage; you can hand-fill marketing/data/sites_manual.csv with crd,url to top up).

Output: marketing/data/sites.csv  (crd, firm, url, source)

Usage:  python b01_resolve_sites.py
"""
import re, csv, collections
import pandas as pd
from b_common import SAMPLE, BROCHURE_TXT, BDATA

BLOCK = re.compile(r"(sec\.gov|adviserinfo|finra\.org|irs\.gov|linkedin|twitter|x\.com|facebook|"
                   r"instagram|youtube|google|adobe|microsoft|apple|schwab\.com|fidelity\.com|"
                   r"morningstar|bloomberg|docusign|calendly|wikipedia)", re.I)
URLRE = re.compile(r"\b((?:https?://)?(?:www\.)?([a-z0-9][a-z0-9\-]{1,50}\.(?:com|net|org|io|co|us|ai|wealth|capital|advisors?|group|llc)))\b", re.I)

def firm_tokens(name):
    return set(re.findall(r"[a-z]{3,}", name.lower()))

def resolve(crd, firm):
    p = BROCHURE_TXT / f"{crd}.txt"
    if not p.exists():
        return None, "no_brochure"
    text = p.read_text(encoding="utf-8", errors="replace")[:8000]  # cover/first pages
    cands = collections.Counter()
    for full, dom in URLRE.findall(text):
        dom = dom.lower()
        if BLOCK.search(dom):
            continue
        cands[dom] += 1
    if not cands:
        return None, "no_url_in_brochure"
    toks = firm_tokens(firm)
    def score(d):
        base = d.split(".")[0]
        name_hit = any(t[:5] in base or base[:5] in t for t in toks if len(t) >= 4)
        return (name_hit, cands[d])
    best = sorted(cands, key=score, reverse=True)[0]
    return f"https://{best}", "brochure"

def main():
    df = pd.read_csv(SAMPLE)
    rows, ok = [], 0
    for _, r in df.iterrows():
        crd, firm = int(r["crd"]), str(r["firm"])
        url, src = resolve(crd, firm)
        if url:
            ok += 1
        rows.append({"crd": crd, "firm": firm, "url": url or "", "source": src})
    # merge optional manual overrides
    man = BDATA / "sites_manual.csv"
    if man.exists():
        m = {int(x["crd"]): x["url"] for x in csv.DictReader(open(man)) if x.get("url")}
        for row in rows:
            if not row["url"] and row["crd"] in m:
                row["url"] = m[row["crd"]]; row["source"] = "manual"; ok += 1
    out = BDATA / "sites.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["crd", "firm", "url", "source"]); w.writeheader()
        w.writerows(rows)
    print(f"[b01] resolved {ok}/{len(rows)} = {ok/len(rows):.0%} websites -> {out}")
    print("[b01] firms with no site are listed with blank url; add crd,url rows to "
          "marketing/data/sites_manual.csv to top up, then rerun.")

if __name__ == "__main__":
    main()
