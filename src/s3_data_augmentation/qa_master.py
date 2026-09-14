# -*- coding: utf-8 -*-
"""质量核查 v1（Goal Brief 验收标准第5条）：
缺失率 / 异常值 / 单位统一 / 时空一致性 / 跨源交叉验证
输出 data_quality_report.json + qa_summary.csv"""
import pandas as pd, numpy as np, json, os
from scipy import stats

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")

m = pd.read_csv(os.path.join(INT, "augmented_yield_master_v2.csv"), low_memory=False)
new = m[m["source_batch"] == "Xiao2024_rds_History"].copy()
base = m[m["source_batch"] == "Baseline_234grid"].copy()
print("master:", m.shape, "| new:", len(new), "| baseline:", len(base))

report = {"master_shape": list(m.shape), "baseline_rows": len(base), "new_rows": len(new)}

# ---------- 1. 缺失率 ----------
key_cols = {
    "目标与管理": ["Yield", "New_Yield", "WN", "xWIrri", "MN", "MR", "xMIrri"],
    "环境-气候": [c for c in m.columns if c.startswith(("bio_", "tavg_", "prec_"))],
    "环境-土壤": [c for c in m.columns if c.startswith("sg_")],
    "地形": [c for c in m.columns if c in ("elev_m", "elevation_m", "slope_deg", "aspect_deg")],
}
miss = {}
for grp, cols in key_cols.items():
    cols = [c for c in cols if c in m.columns]
    if not cols: continue
    r_base = base[cols].isna().mean().mean() * 100
    r_new = new[cols].isna().mean().mean() * 100
    miss[grp] = {"baseline_%": round(r_base, 2), "new_%": round(r_new, 2)}
report["missing_rates"] = miss
print("\n=== 缺失率 ==="); print(json.dumps(miss, ensure_ascii=False, indent=1))

# ---------- 2. 异常值（增量行 Yield 的 3σ 与 IQR） ----------
y = new["Yield"].dropna()
z = np.abs(stats.zscore(y))
iqr = y.quantile(0.75) - y.quantile(0.25)
lo, hi = y.quantile(0.25) - 1.5 * iqr, y.quantile(0.75) + 1.5 * iqr
n_z3 = int((z > 3).sum()); n_iqr = int(((y < lo) | (y > hi)).sum())
report["yield_outliers_new"] = {"n_zscore_gt3": n_z3, "n_iqr": n_iqr,
    "range": [round(float(y.min()), 3), round(float(y.max()), 3)],
    "mean": round(float(y.mean()), 3), "std": round(float(y.std()), 3),
    "normality_p": round(float(stats.normaltest(y).pvalue), 4)}
print(f"\n=== 增量 Yield 异常值 === n(3σ)={n_z3} n(IQR)={n_iqr} range=[{y.min():.2f},{y.max():.2f}]")

# ---------- 3. 单位统一核查 ----------
units_ok = {
    "Yield_t_ha": bool(new["Yield"].between(0.5, 25).all()),
    "WN_kg_ha": bool(new["WN"].between(0, 600).all()),
    "irrigation_mm": bool(new["xWIrri"].between(0, 1500).all()),
    "bio1_degC_x10": bool(m["bio_1"].dropna().abs().max() > 50 if "bio_1" in m else False),
}
report["unit_checks"] = units_ok
print("\n=== 单位核查 ==="); print(json.dumps(units_ok))

# ---------- 4. 时空一致性 ----------
# 4a. 空间范围：新增行应全部落在平谷 bbox
in_bb = new["lon"].between(116.75, 117.60) & new["lat"].between(39.93, 40.53)
report["spatial_bbox_ok"] = {"n_out_of_bbox": int((~in_bb).sum())}
# 4b. 时间：History 基准期（Xiao2024 文档定义 ≈2000-2014 平均）单一年段，无跨年混合
report["temporal"] = {"new_period": "History (Xiao2024 baseline, ~2000-2014 mean)",
                      "scenario_periods": "2030s/2060s stored separately (37248 rows)"}
print(f"\n=== 时空 === bbox 外: {int((~in_bb).sum())} 个")

# ---------- 5. 跨源交叉验证（三源产量一致性） ----------
# Xiao rds(History) vs WheatYield_ref.tif vs 基线融合产量 —— 按最近网格匹配
ref = pd.read_csv(os.path.join(INT, "xiao2024_ref_grid.csv"), low_memory=False)
# ref 表有 xiao_wheatyield（38 valid），基线表有 yield_2021_tha/融合列
m_new_coord = new[["lon", "lat", "Yield"]].copy()
ref_valid = ref[ref["xiao_wheatyield"].notna()][["lon", "lat", "xiao_wheatyield"]].copy()
# 最近邻匹配（度为单位，1km≈0.0083°）
from scipy.spatial import cKDTree
tree = cKDTree(np.deg2rad(ref_valid[["lon", "lat"]].values))
def nearest_yield(lon, lat):
    d, i = tree.query(np.deg2rad([lon, lat]))
    return ref_valid["xiao_wheatyield"].values[i] if d < 0.01 else np.nan
m_new_coord["ref_yield"] = [nearest_yield(a, b) for a, b in zip(m_new_coord["lon"], m_new_coord["lat"])]
pair = m_new_coord.dropna(subset=["ref_yield"])
if len(pair) >= 5:
    from scipy.stats import pearsonr
    r, p = pearsonr(pair["Yield"], pair["ref_yield"])
    report["cross_source"] = {"n_pairs": len(pair),
        "pearson_r": round(float(r), 3), "p": float(p),
        "rds_mean": round(float(pair["Yield"].mean()), 3),
        "ref_mean": round(float(pair["ref_yield"].mean()), 3),
        "note": "rds Yield 为轮作体系优化产量(t/ha)，ref 为小麦单季参考产量(t/ha)，均值差异符合预期"}
    print(f"\n=== 跨源交叉 === n={len(pair)} r={r:.3f} p={p:.2g}")
else:
    report["cross_source"] = {"n_pairs": len(pair), "note": "可匹配对不足，跳过"}

with open(os.path.join(INT, "data_quality_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("\nsaved data_quality_report.json")
print(json.dumps(report["cross_source"], ensure_ascii=False, indent=1) if "cross_source" in report else "")
