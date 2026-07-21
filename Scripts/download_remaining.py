#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Try to download remaining data from figshare and CHELSA"""
import urllib.request, json, os

results = {}

# 1. Figshare management data
print("=== 1. FIGSHARE Management Data ===")
try:
    url = "https://api.figshare.com/v2/articles/24471919"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    title = data.get("title", "?")
    print(f"  Title: {title}")
    files = data.get("files", [])
    print(f"  Files: {len(files)}")
    mgmt_dir = r"D:\2026-SP\Data\Management"
    os.makedirs(mgmt_dir, exist_ok=True)
    for f in files:
        fname = f.get("name", "?")
        fsize = f.get("size", 0)
        furl = f.get("download_url", "")
        print(f"    {fname} ({fsize/1024/1024:.1f}MB)")
        if any(fname.endswith(ext) for ext in [".tif", ".nc", ".csv", ".rds"]):
            dest = os.path.join(mgmt_dir, fname)
            if os.path.exists(dest) and os.path.getsize(dest) > 100:
                print(f"      [SKIP] exists")
                continue
            try:
                req2 = urllib.request.Request(furl, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=120) as r2:
                    fdata = r2.read()
                with open(dest, "wb") as fw:
                    fw.write(fdata)
                print(f"      [OK] {len(fdata)/1024/1024:.1f}MB -> {dest}")
            except Exception as e:
                print(f"      [FAIL] {e.__class__.__name__}")
    results["figshare"] = "OK"
except Exception as e:
    print(f"  [FAIL] figshare: {e.__class__.__name__}: {str(e)[:100]}")
    results["figshare"] = f"FAIL: {e.__class__.__name__}"

# 2. CHELSA
print("\n=== 2. CHELSA Extreme Climate ===")
try:
    url = "https://chelsa-climate.org/downloads/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"  Accessible: HTTP {r.status}")
    results["chelsa"] = "OK - accessible"
except Exception as e:
    print(f"  [FAIL] CHELSA: {e.__class__.__name__}")
    results["chelsa"] = f"FAIL: {e.__class__.__name__}"

# 3. China Soil Database
print("\n=== 3. China Soil Database ===")
try:
    url = "http://poles.tpdc.ac.cn/zh-hans/data/8ba0a731-5b0b-4e2f-8b95-8b29cc3c0f3a/"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"  Accessible: HTTP {r.status}")
    results["china_soil"] = "OK - accessible"
except Exception as e:
    print(f"  [FAIL] China Soil: {e.__class__.__name__}")
    results["china_soil"] = f"FAIL: {e.__class__.__name__}"

# 4. ISRIC SoilGrids
print("\n=== 4. ISRIC SoilGrids ===")
try:
    url = "https://www.isric.org/explore/soilgrids"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print(f"  Accessible: HTTP {r.status}")
    results["soilgrids"] = "OK - accessible"
except Exception as e:
    print(f"  [FAIL] ISRIC: {e.__class__.__name__}")
    results["soilgrids"] = f"FAIL: {e.__class__.__name__}"

# Summary
print("\n" + "="*50)
print("CONNECTIVITY SUMMARY")
print("="*50)
for k, v in results.items():
    status = "OK" if "OK" in str(v) else "BLOCKED"
    print(f"  {k}: {status} ({v})")
