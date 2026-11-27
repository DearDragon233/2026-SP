# -*- coding: utf-8 -*-
"""W57 round 2: title lookups for entries without a DOI; retry the rate-limited ones."""
import re, json, time, urllib.request, urllib.parse
s = open(r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md', encoding='utf-8').read()
refs = s[s.find('## References'):]
entries = dict(re.findall(r'^(\d+)\. (.+)$', refs, flags=re.M))
UA = {'User-Agent': '2026-SP-manuscript-check (mailto:research@example.org)'}
def get(url):
    last = "unknown"
    for k in range(6):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(20 * (k + 1)); continue
            return {"_err": f"HTTP {e.code}"}
        except Exception as e:
            time.sleep(4); last = f"{type(e).__name__}"
    return {"_err": last}
def strip(t): return re.sub(r'\*|$', '', t)
targets = {
 2: "Ray Gerber MacDonald West Climate variation explains a third of global crop yield variability Nature Communications 2015",
 3: "van Klompenburg Kassahun Catal Crop yield prediction using machine learning A systematic literature review Computers and Electronics in Agriculture 2020",
 5: "Li Yu Du Liu Tracking spatiotemporal dynamics of crop-specific areas through machine learning and statistics disaggregating Scientific Data",
 7: "Kallenberg Paudel CY-Bench comprehensive benchmark dataset sub-national crop yield forecasting Earth System Science Data 2026",
 8: "Roberts Bahn Ciuti Cross-validation strategies for data with temporal spatial hierarchical or phylogenetic structure Ecography 2017",
 9: "Ploton Mortier Spatial validation reveals poor predictive performance of large-scale ecological mapping models Nature Communications 2020",
 10: "Meyer Pebesma Machine learning-based global maps of ecological variables and the challenge of assessing them Nature Communications 2022",
 11: "Wadoux Heuvelink de Bruin Brus Spatial cross-validation is not the right way to evaluate map accuracy Ecological Modelling 2021",
 12: "Raudaschl subsampling strategy cross-validation spatially autocorrelated data Ecological Modelling",
 13: "Zhao Xiao Bai prediction of wheat yield in the North China Plain by coupling crop model with machine learning algorithms Agriculture 2023",
}
out = {}
for num, q in targets.items():
    d = get("https://api.crossref.org/works?rows=2&query.bibliographic=" + urllib.parse.quote(q))
    items = d.get("message", {}).get("items", []) if "_err" not in d else []
    if not items:
        print(f"[{num}] LOOKUP FAILED: {d.get('_err')}"); out[num] = {"status": "failed", "err": d.get("_err")}; time.sleep(3); continue
    w = items[0]
    t = (w.get("title") or [""])[0]; au = [a.get("family", "") for a in w.get("author", [])][:4]
    yr = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
    cont = (w.get("container-title") or [""])[0]
    rec = {"status": "found", "doi": w.get("DOI"), "title": t, "authors": au, "year": yr, "journal": cont,
           "volume": w.get("volume"), "issue": w.get("issue"), "page": w.get("page") or w.get("article-number")}
    out[num] = rec
    ours = entries[str(num)]
    # agreement checks
    fam = re.findall(r'([A-Z][A-Za-z\-]+), [A-Z]\.', ours)
    fa_ok = bool(fam and au and fam[0].lower().replace("van ", "") == au[0].lower().replace("van ", ""))
    yr_ours = re.search(r'\*?[A-Z][^*]*?\*?\s(\d{4})', ours)
    yr_ok = bool(yr_ours and yr and yr_ours.group(1) == str(yr))
    words = [x for x in re.findall(r'[A-Za-z]{5,}', t) if x.lower() not in ("using", "based", "study", "analysis")]
    hit = sum(1 for x in words if x.lower() in ours.lower())
    rec.update(first_author_ok=fa_ok, year_ok=yr_ok, year_ours=yr_ours.group(1) if yr_ours else None,
               title_overlap=f"{hit}/{len(words)}")
    print(f"[{num}] {au} {yr} | {cont} {w.get('volume')}({w.get('issue')}) {rec['page']} | doi {w.get('DOI')}")
    print(f"      CrossRef: {t[:120]}")
    print(f"      first-author ok={fa_ok}  year ok={yr_ok} (ours {rec['year_ours']})  title overlap={rec['title_overlap']}")
    time.sleep(6)
json.dump(out, open(r'D:\2026-SP\Outputs\reports\w57_doi_check_round2.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
