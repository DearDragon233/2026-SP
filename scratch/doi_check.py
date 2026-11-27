# -*- coding: utf-8 -*-
"""W57: verify every reference of paper 2 against CrossRef."""
import re, json, time, urllib.request, urllib.parse
s = open(r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md', encoding='utf-8').read()
refs = s[s.find('## References'):]
entries = re.findall(r'^(\d+)\. (.+)$', refs, flags=re.M)
print(f"{len(entries)} reference entries\n")
UA = {'User-Agent': '2026-SP-manuscript-check (mailto:research@example.org)'}
def crossref(q):
    url = "https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(q)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)["message"]["items"]
    except Exception as e:
        return [{"_err": f"{type(e).__name__}: {e}"}]
def by_doi(d):
    try:
        req = urllib.request.Request("https://api.crossref.org/works/" + urllib.parse.quote(d), headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)["message"]
    except Exception as e:
        return {"_err": f"{type(e).__name__}: {e}"}
out = []
for num, text in entries:
    m = re.search(r'DOI: (\S+?)\.?$', text)
    res = {"num": int(num), "text": text}
    if m:
        d = m.group(1).rstrip('.')
        w = by_doi(d)
        if "_err" in w:
            res.update(status="DOI-LOOKUP-FAILED", detail=w["_err"])
        else:
            t = (w.get("title") or [""])[0]
            au = [f"{a.get('family','')}" for a in w.get("author", [])][:3]
            yr = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
            cont = (w.get("container-title") or [""])[0]
            res.update(status="FOUND", doi=d, cr_title=t, cr_authors=au, cr_year=yr, cr_journal=cont,
                       cr_volume=w.get("volume"), cr_page=w.get("page") or w.get("article-number"))
            first = re.match(r'([A-Z][a-zA-Z\-]+),', text)
            fam_ok = bool(first and au and first.group(1).lower() == au[0].lower())
            res["first_author_match"] = fam_ok
            key = re.sub(r'[^a-z]', '', t.lower()[:40])
            res["title_words_in_ours"] = all(wd in text.lower() for wd in re.findall(r'[A-Za-z]{5,}', t)[:4])
    else:
        res.update(status="NO-DOI-IN-ENTRY")
    out.append(res)
    print(f"[{num}] {res['status']}", flush=True)
    if res["status"] == "FOUND":
        print("     ours :", text[:150])
        print("     CrossRef:", res["cr_authors"], res["cr_year"], "|", res["cr_title"][:110], "|", res["cr_journal"], res["cr_volume"], res["cr_page"])
        print("     first-author match:", res["first_author_match"], "| title words present:", res["title_words_in_ours"])
    else:
        print("     ours :", text[:160]); print("     detail:", res.get("detail", ""))
    time.sleep(1.2)
json.dump(out, open(r'D:\2026-SP\Outputs\reports\w57_doi_check.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
