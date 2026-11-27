# -*- coding: utf-8 -*-
"""W57 round 3: direct DOI lookups, long spacing (CrossRef rate-limits bursts)."""
import re, json, time, urllib.request, urllib.parse
UA = {'User-Agent': '2026-SP-manuscript-check (mailto:research@example.org)'}
# candidate DOIs for the entries lacking one; every one is looked up, none is trusted
CAND = {
 2:  "10.1038/ncomms6989",
 3:  "10.1016/j.compag.2020.105709",
 5:  "10.1038/s41597-025-05572-x",
 7:  "10.5194/essd-18-3997-2026",
 8:  "10.1111/ecog.02881",
 10: "10.1038/s41467-022-29838-9",
 12: "10.1016/j.ecolmodel.2021.109920",
 13: "10.3390/agriculture13010099",
}
def by_doi(d):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(d)
    last = None
    for k in range(8):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=50) as r:
                return json.load(r)["message"], None
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 404: return None, "404 not in CrossRef"
            if e.code == 429: time.sleep(25 * (k + 1)); continue
            time.sleep(8)
        except Exception as e:
            last = type(e).__name__; time.sleep(10)
    return None, last
out = {}
for num, d in CAND.items():
    w, err = by_doi(d)
    if w is None:
        print(f"[{num}] {d} -> LOOKUP FAILED ({err})", flush=True); out[num] = {"doi": d, "status": "failed", "err": err}
    else:
        t = (w.get("title") or [""])[0]
        au = [a.get("family", "") for a in w.get("author", [])][:3]
        yr = (w.get("issued", {}).get("date-parts") or [[None]])[0][0]
        cont = (w.get("container-title") or [""])[0]
        rec = {"doi": w.get("DOI"), "status": "found", "title": t, "authors": au, "year": yr, "journal": cont,
               "volume": w.get("volume"), "issue": w.get("issue"),
               "page": w.get("page") or w.get("article-number")}
        out[num] = rec
        print(f"[{num}] {au} {yr} | {cont} {w.get('volume')}({w.get('issue')}) {rec['page']} | {w.get('DOI')}", flush=True)
        print(f"      {t[:125]}", flush=True)
    time.sleep(9)
json.dump(out, open(r'D:\2026-SP\Outputs\reports\w57_doi_check_round3.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
