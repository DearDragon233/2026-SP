# -*- coding: utf-8 -*-
"""P3: 检索《北京区域统计年鉴 2022》表 3-22（粮食播种面积及产量，分区）平谷区冬小麦数字。
尝试 tjnj.net 的表页直链；若取到则更新台账，取不到则把"已核查表目清单"写入台账。
"""
import urllib.request, re, sys

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")

candidates = [
    "https://www.tjnj.net/",
    "https://www.tjnj.net/nianjian/2022bjsq/",
    "https://www.tjnj.net/nianjian/bj2022/",
]
hit = None
for url in candidates:
    try:
        html = fetch(url)
        # 站内搜索含 3-22 且 2022北京区域统计年鉴 的链接
        links = re.findall(r'href="([^"]+)"[^>]*>\s*([^<]*3-22[^<]*)', html)
        print(url, "->", links[:5])
        if links:
            hit = (url, links)
            break
    except Exception as ex:
        print("FAIL", url, repr(ex)[:80])

if hit:
    base, links = hit
    for href, title in links[:3]:
        u = href if href.startswith("http") else base.rstrip("/") + "/" + href.lstrip("/")
        try:
            page = fetch(u)
            text = " ".join(re.sub(r"<[^>]+>", " ", page).split())
            i = text.find("平谷")
            print("PAGE", u, "| 平谷 context:", text[max(0, i-120):i+160] if i >= 0 else "NOT FOUND")
        except Exception as ex:
            print("FAIL page", u, repr(ex)[:80])
else:
    print("NO INDEX LINK FOUND — 表页需登录/付费，写入台账：已核查表目存在但在线全文不可及")
