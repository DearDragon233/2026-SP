# -*- coding: utf-8 -*-
"""时序增强（Goal Brief 验收第3条）：
A. NASA POWER 逐月 T2M/PRECTOTCORR（平谷中心 117.1E/40.15N，2000-2021，公有领域）
   → 每年生长季（10-6月冬小麦）均温/降水/积温 → 22 年真实年际变化协变量
B. Xiao2024 三时期面板聚合（History/2030s/2060s × GCM × SSP）→ 时序覆盖对照表
输出：
  pinggu_climate_timeseries_2000_2021.csv
  xiao_scenario_panel_summary.csv / timeseries_coverage_table.csv
"""
import urllib.request, json, ssl, os, time
import pandas as pd, numpy as np

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
ctx = ssl.create_default_context()
ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE

# ---------- A. NASA POWER monthly 2000-2021 ----------
url = ("https://power.larc.nasa.gov/api/temporal/monthly/point?"
       "parameters=T2M,PRECTOTCORR&community=AG&longitude=117.1&latitude=40.15"
       "&start=20000101&end=20211231&format=JSON")
cache = os.path.join(INT, "nasa_power_pinggu_2000_2021.json")
if os.path.exists(cache):
    print("using cached NASA POWER json")
    data = json.load(open(cache, encoding="utf-8"))
else:
    data = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
                data = json.loads(r.read().decode())
            json.dump(data, open(cache, "w", encoding="utf-8"))
            print("NASA POWER fetched OK")
            break
        except Exception as e:
            print(f"  attempt {attempt+1} failed: {type(e).__name__}: {str(e)[:80]}")
            time.sleep(5)
    if data is None:
        raise SystemExit("NASA POWER unreachable after 3 attempts")

prop = data["properties"]["parameter"]
t2m, prec = prop["T2M"], prop["PRECTOTCORR"]
rows = []
for key in sorted(t2m.keys()):  # YYYYMM
    year, month = int(key[:4]), int(key[4:])
    rows.append({"year": year, "month": month,
                 "t2m_c": t2m[key], "prec_mm": prec[key]})
ts = pd.DataFrame(rows)
print("monthly rows:", len(ts), "| years:", ts["year"].nunique(),
      f"({ts['year'].min()}-{ts['year'].max()})")
# 缺失值标记（NASA POWER 用 -999）
ts.replace(-999.0, np.nan, inplace=True)
print("T2M valid:", ts["t2m_c"].notna().sum(), "| PREC valid:", ts["prec_mm"].notna().sum())

# 生长季聚合：冬小麦 10月(当年)-次年6月 → 归属收割年
ts = ts.sort_values(["year", "month"]).reset_index(drop=True)
ts["season_year"] = np.where(ts["month"] >= 10, ts["year"] + 1, ts["year"])
ws = ts[ts["month"].isin([10, 11, 12, 1, 2, 3, 4, 5, 6])]
gs = ws.groupby("season_year").agg(
    tmean_ws=("t2m_c", "mean"), prec_ws_mm=("prec_mm", "sum"),
    gdd0_ws=("t2m_c", lambda x: float(np.nansum(np.maximum(x - 0, 0)) * 30.4)))
gs = gs[(gs.index >= 2001) & (gs.index <= 2021)].reset_index().rename(columns={"season_year": "year"})
gs.round(3).to_csv(os.path.join(INT, "pinggu_climate_timeseries_2000_2021.csv"),
                   index=False, encoding="utf-8-sig")
print("growing-season series:", len(gs), "years ->", f"{gs['year'].min()}-{gs['year'].max()}")
print(gs.head(3).to_string(index=False))

# ---------- B. Xiao 三时期面板 ----------
scen = pd.read_csv(os.path.join(INT, "xiao2024_pinggu_full_scenarios.csv"), low_memory=False)
hist = pd.read_csv(os.path.join(INT, "xiao2024_rds_pinggu_raw.csv"), low_memory=False)
hist = hist[hist["Period"] == "History"]
print("\nscenario rows:", len(scen), "| history rows:", len(hist))

# 基准期（每格 1 行）
h_summary = {"period": "History (基准期≈2000-2014)", "n_cells": hist["gridcell"].nunique(),
             "n_rows": len(hist), "yield_mean": round(hist["Yield"].mean(), 3),
             "yield_min": round(hist["Yield"].min(), 3), "yield_max": round(hist["Yield"].max(), 3),
             "WN_mean": round(hist["WN"].mean(), 1), "xWIrri_mean": round(hist["xWIrri"].mean(), 1)}
# 情景期（每格 24 行 = 6GCM×2SSP×2时期）
s_summary = (scen.groupby(["Period", "SSP"])
             .agg(n_rows=("Yield", "size"), yield_mean=("Yield", "mean"),
                  yield_min=("Yield", "min"), yield_max=("Yield", "max"),
                  WN_mean=("WN", "mean"), xWIrri_mean=("xWIrri", "mean"))
             .round(3).reset_index())
s_summary["n_cells"] = scen.groupby(["Period", "SSP"])["gridcell"].nunique().values

cov = pd.DataFrame([h_summary])
cov = pd.concat([cov, s_summary.rename(columns={"Period": "period"})], ignore_index=True, sort=False)
cov.to_csv(os.path.join(INT, "timeseries_coverage_table.csv"), index=False, encoding="utf-8-sig")
print("\n=== 时序覆盖对照表 ===")
print(cov.to_string(index=False))

# ---------- C. 2000-2021 年际变率 vs 基线气候背景的对比说明 ----------
base_bio1 = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))["bio_1"].mean()
print(f"\n对比：WorldClim bio_1(1970-2000 背景) = {base_bio1/10:.2f}°C | "
      f"NASA POWER 2001-2021 生长季均温均值 = {gs['tmean_ws'].mean():.2f}°C")
print("年际波动 std =", round(gs["tmean_ws"].std(), 3), "°C /",
      round(gs["prec_ws_mm"].std(), 1), "mm —— 这是静态背景图层没有的真实时序信息")
