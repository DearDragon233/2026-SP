# -*- coding: utf-8 -*-
"""P3: tjnj.net 站内搜索定位《北京区域统计年鉴 2022》表 3-22（粮食播种面积及产量，分区）。
抓到平谷区数字 → 更新台账 R5；抓不到 → 台账记录"表目已确认存在、在线全文需登录/付费"。
"""
import urllib.request, re, json, sys

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")

base = "https://www.tjnj.net"
results = {"queries": [], "found": False}

# 1) 站内搜索接口（dedecms 常用 /plus/search.php）
for q in ["2022北京区域统计年鉴 3-22", "北京区域统计年鉴 粮食播种面积及产量情况"]:
    u = base + "/plus/search.php?keyword=" + urllib.parse.quote(q)
    try:
        html = fetch(u)
        links = re.findall(r'href="([^"]+)"[^>]*>([^<]*(?:3-22|粮食播种面积)[^<]*)', html)
        results["queries"].append({"q": q, "links": links[:5]})
        print("SEARCH", q, "->", links[:5])
        if links:
            for href, title in links[:3]:
                u2 = href if href.startswith("http") else base + href
                try:
                    page = fetch(u2)
                    text = " ".join(re.sub(r"<[^>]+>", " ", page).split())
                    i = text.find("平谷")
                    ctx = text[max(0, i-150):i+200] if i >= 0 else ""
                    print("  PAGE", u2, "|", ctx[:260])
                    if i >= 0 and ("吨" in ctx or "公顷" in ctx):
                        results["found"] = True
                        results["context"] = ctx
                        results["url"] = u2
                        break
                except Exception as ex:
                    print("  FAIL page", repr(ex)[:60])
            if results["found"]:
                break
    except Exception as ex:
        print("FAIL search", q, repr(ex)[:60])

json.dump(results, open(r"D:\2026-SP\Outputs\intermediate\w16_p3_yearbook_hunt.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("hunt saved; found =", results["found"])
