"""
b02_crawl_marketing.py — politely crawl each firm's marketing site and extract text.

Fetches the homepage + up to N same-domain pages whose link text/URL suggests AI/tech/approach
content (about, technology, approach, investment process, ai, insights). Extracts main text
with trafilatura. Saves one text file per firm; logs coverage.

Output: marketing/data/marketing_text/{crd}.txt   +   marketing/out/marketing_crawl_log.csv

Usage:  pip install trafilatura beautifulsoup4 ; python b02_crawl_marketing.py
"""
import csv, re
from urllib.parse import urljoin, urlparse
import pandas as pd
from b_common import BDATA, BOUT, web_get, persist_raw_b

from bs4 import BeautifulSoup   # required (installs cleanly)
try:
    import trafilatura           # optional; better main-text extraction
    _HAS_TRAF = True
except Exception:
    _HAS_TRAF = False
    print("[b02] trafilatura unavailable -> using BeautifulSoup fallback "
          "(fine for classification; `pip install lxml_html_clean` re-enables trafilatura)")

SITES = BDATA / "sites.csv"
MTXT = BDATA / "marketing_text"; MTXT.mkdir(exist_ok=True)
KEYPAGES = re.compile(r"about|technolog|approach|process|philosoph|invest|method|ai|artificial|"
                      r"machine|data|insight|research|our-firm|how-we|capabilit", re.I)

def _bs4_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        t.decompose()
    return re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))

def extract(html, url):
    if _HAS_TRAF:
        t = trafilatura.extract(html, url=url, include_comments=False, favor_recall=True)
        if t:
            return t
    try:
        return _bs4_text(html)
    except Exception:
        return ""

MAX_PAGES = 8
THIN = 150
COMMON_PATHS = ["/about", "/about-us", "/our-firm", "/firm", "/who-we-are", "/approach",
                "/investment-approach", "/our-approach", "/process", "/investment-process",
                "/technology", "/philosophy", "/services", "/what-we-do"]

def same_domain(a, b):
    return urlparse(a).netloc.replace("www.", "") == urlparse(b).netloc.replace("www.", "")

def _fetch_html(url):
    r = web_get(url)
    if r is not None and r.status_code == 200 and "html" in r.headers.get("content-type", "").lower():
        return r
    return None

def _home_variants(url):
    p = urlparse(url if "://" in url else "https://" + url)
    host = p.netloc or p.path
    bare = host.replace("www.", "")
    hosts = [host, bare, "www." + bare]
    out = []
    for scheme in ("https", "http"):
        for h in dict.fromkeys(hosts):
            out.append(f"{scheme}://{h}/")
    return list(dict.fromkeys(out))

def crawl(url):
    # 1) find a working homepage across scheme/www variants
    home, r = None, None
    for cand in _home_variants(url):
        r = _fetch_html(cand)
        if r:
            home = str(r.url); break
    if not home:
        return "", 0
    texts, seen = [], {home}
    persist_raw_b("marketing_html", f"{urlparse(home).netloc}_home.html", r.content, home)
    texts.append(extract(r.text, home))
    # 2) gather candidate subpages: homepage links + common paths + sitemap
    cands = []
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = urljoin(home, a["href"])
            if same_domain(home, href) and href not in seen and KEYPAGES.search(a.get_text(" ") + " " + href):
                cands.append(href.split("#")[0])
    except Exception:
        pass
    for path in COMMON_PATHS:
        cands.append(urljoin(home, path))
    sm = web_get(urljoin(home, "/sitemap.xml"))
    if sm is not None and sm.status_code == 200:
        for loc in re.findall(r"<loc>([^<]+)</loc>", sm.text)[:200]:
            if KEYPAGES.search(loc):
                cands.append(loc)
    # 3) fetch up to MAX_PAGES unique candidates
    for href in dict.fromkeys(cands):
        if len(seen) >= MAX_PAGES:
            break
        if href in seen:
            continue
        seen.add(href)
        rr = _fetch_html(href)
        if rr:
            texts.append(extract(rr.text, href))
    full = "\n\n---PAGE---\n\n".join(t for t in texts if t and len(t.strip()) > 30)
    return full, len(seen)

def main():
    if not SITES.exists():
        raise SystemExit("[b02] run b01_resolve_sites.py first.")
    df = pd.read_csv(SITES)
    log, ok = [], 0
    n = len(df)
    for i, r in df.iterrows():
        crd = int(r["crd"]); url = str(r.get("url") or "").strip()
        out = MTXT / f"{crd}.txt"
        if out.exists() and out.stat().st_size > 0:
            ok += 1; log.append({"crd": crd, "status": "cached", "chars": out.stat().st_size}); continue
        if not url or url == "nan":
            log.append({"crd": crd, "status": "no_url", "chars": 0})
            print(f"[b02] {i+1}/{n} crd={crd} no_url", flush=True); continue
        try:
            text, npages = crawl(url)
        except Exception as e:
            log.append({"crd": crd, "status": f"error:{type(e).__name__}", "chars": 0})
            print(f"[b02] {i+1}/{n} crd={crd} ERROR", flush=True); continue
        if len(text) < THIN:
            log.append({"crd": crd, "status": "thin", "chars": len(text)})
            print(f"[b02] {i+1}/{n} crd={crd} thin ({len(text)})", flush=True); continue
        out.write_text(text, encoding="utf-8")
        ok += 1; log.append({"crd": crd, "status": f"ok({npages}pg)", "chars": len(text)})
        print(f"[b02] {i+1}/{n} crd={crd} ok ({len(text)} chars)", flush=True)
    with open(BOUT / "marketing_crawl_log.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["crd", "status", "chars"]); w.writeheader(); w.writerows(log)
    print(f"[b02] usable marketing text for {ok}/{n} = {ok/n:.0%} firms "
          f"(need >=300 for the split). -> marketing/out/marketing_crawl_log.csv")

if __name__ == "__main__":
    main()
