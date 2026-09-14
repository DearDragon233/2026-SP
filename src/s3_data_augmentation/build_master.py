# -*- coding: utf-8 -*-
"""构建翻倍主数据集：
- 基线：234 网格（data_with_yield_ensemble_full.csv，3.5km 聚合网格）
- 增量：Xiao2024 Allregions.rds 平谷 1552 个 1km 网格 × History 基准期
  （优化产量 Yield、优化施氮 WN/xWIrri、土壤气候协变量，CC BY 4.0）
- 在 1552 网格位置采样本地环境栅格（WorldClim/SoilGrids/SRTM）→ 环境指纹对齐
输出：
  augmented_yield_master.csv       主数据集（234 基线 + 1552 增量，来源批次标注）
  xiao2024_pinggu_full_scenarios.csv  2030s/2060s 情景数据（单独存放，不混入主表）
"""
import pyreadr, rasterio, numpy as np, pandas as pd, os
from pyproj import Transformer

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
LON0, LAT1, RES, NCOL = 112.1, 40.7, 0.008333333333333333, 1320

# ---------- 1. rds 平谷子集（复用已验证的映射） ----------
ping = pd.read_csv(os.path.join(INT, "xiao2024_rds_pinggu_raw.csv"), low_memory=False)
hist = ping[ping["Period"] == "History"].copy()
print("History rows:", len(hist), "| unique cells:", hist["gridcell"].nunique())

# ---------- 2. 环境栅格定义（与 fine250 管线同源） ----------
WC = os.path.join(ROOT, "Data", "WorldClim")
SG = os.path.join(ROOT, "Data", "SoilGrids_wgs84")
ST = os.path.join(ROOT, "Data", "SRTM", "srtm_60_04.tif")

def sample(path, lons, lats, nodata_filter=1e30, label=""):
    """点采样：返回 (n,) 数组；支持投影栅格（自动转换坐标）"""
    with rasterio.open(path) as src:
        if str(src.crs) != "EPSG:4326":
            tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            xs, ys = tr.transform(lons, lats)
        else:
            xs, ys = lons, lats
        arr = src.read(1)
        out = np.full(len(xs), np.nan)
        H, W = arr.shape
        for i, (x, y) in enumerate(zip(xs, ys)):
            try:
                r_, c_ = src.index(x, y)
                if 0 <= r_ < H and 0 <= c_ < W:
                    v = float(arr[r_, c_])
                    if not (nodata_filter is not None and abs(v) > nodata_filter):
                        if src.nodata is not None and v == src.nodata:
                            continue
                        out[i] = v
            except Exception:
                pass
        nv = out[~np.isnan(out)]
        print(f"  {label}: valid {len(nv)}/{len(out)}")
        return out

lons = hist["lon"].values; lats = hist["lat"].values
env = pd.DataFrame({"gridcell": hist["gridcell"].values, "lon": lons, "lat": lats})

# WorldClim bio（2.5 arcmin ≈5km：气候背景）
for i in range(1, 20):
    env[f"bio_{i}"] = np.round(sample(os.path.join(WC, f"wc2.1_2.5m_bio_{i}.tif"), lons, lats, label=f"bio_{i}"), 4)
# 月值 tavg/prec（气候背景）
for m in range(1, 13):
    env[f"tavg_{m:02d}"] = np.round(sample(os.path.join(WC, f"wc2.1_2.5m_tavg_{m:02d}.tif"), lons, lats, label=f"tavg_{m:02d}"), 4)
    env[f"prec_{m:02d}"] = np.round(sample(os.path.join(WC, f"wc2.1_2.5m_prec_{m:02d}.tif"), lons, lats, label=f"prec_{m:02d}"), 4)
# SoilGrids（ESRI:54052，5km 聚合版）
for v in ["clay", "sand", "silt", "soc", "bdod", "cec", "ph", "nitrogen"]:
    p = os.path.join(SG, f"{v}.tif")
    if os.path.exists(p):
        env[f"sg_{v}"] = np.round(sample(p, lons, lats, label=f"sg_{v}"), 4)
# SRTM 地形（90m，真实 1km 尺度信息）
env["elev_m"] = np.round(sample(ST, lons, lats, label="srtm_elev"), 2)

print("env matrix:", env.shape)

# ---------- 3. 合并 Xiao 目标与管理变量 ----------
keep = ["gridcell", "lon", "lat", "CO2", "SAT_1", "BD_1", "SOC_1", "PH_1",
        "WN", "WR", "xWIrri", "MN", "MR", "xMIrri", "Yield", "WMSOC", "New_Yield"]
aug = hist[keep].merge(env, on="gridcell", suffixes=("_rds", ""))
# lon/lat 用我们反算的（更精确一致）
aug["lon"] = aug["lon_rds"]; aug["lat"] = aug["lat_rds"]
aug.drop(columns=[c for c in ["lon_rds", "lat_rds"] if c in aug.columns], inplace=True)

# 来源批次标注
aug["source_batch"] = "Xiao2024_rds_History"
aug["yield_unit"] = "t/ha(rotation, optimized)"
aug["license"] = "CC BY 4.0"
print("augmented:", aug.shape)

# ---------- 4. 基线 234 表 + 增量表 → 主数据集 ----------
base = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
base["source_batch"] = "Baseline_234grid"
base["license"] = "internal + Xiao2024(CC BY 4.0)"
print("baseline:", base.shape)

master = pd.concat([base, aug], ignore_index=True, sort=False)
master.to_csv(os.path.join(INT, "augmented_yield_master.csv"), index=False, encoding="utf-8-sig")
print("\n=== MASTER ===", master.shape)
print("  baseline rows:", len(base), "+ new rows:", len(aug),
      "=", len(master), f"({len(master)/len(base):.1f}x baseline)")

# 情景数据单独保存（2030s/2060s，不混入主表）
scen = ping[ping["Period"] != "History"].copy()
scen["source_batch"] = "Xiao2024_rds_" + scen["Period"]
scen.to_csv(os.path.join(INT, "xiao2024_pinggu_full_scenarios.csv"), index=False, encoding="utf-8-sig")
print("scenarios saved:", scen.shape)
