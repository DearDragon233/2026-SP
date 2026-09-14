# -*- coding: utf-8 -*-
"""W15-F2/F3/F4 实验包：
F2. 24 变量 PCA：PC1 解释方差、有效维数（80% 累计）、PC1-PC5 逐轴对目标 A 回归
F3. SRTM 三变量 18 格缺失定位（地形分布特征）+ 分列缺失表 + KNN 插补版本
F4. GDD 基准温度/窗口文档化验证（从数据反推 Tbase）
输出: w15_f2_pca.csv/json, w15_f3_missing_table.csv, w15_f4_gdd_doc.json
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.impute import KNNImputer
from sklearn.model_selection import KFold

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
df = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble.csv"))
coords = df[["lon", "lat"]].values
yA = df["wheat_yield_tha"].values
yC = df["yield_blended_tha"].values
m43 = ~np.isnan(yA)

drop = {"lon", "lat", "wheat_yield_tha", "wheat_yield_pred_tha", "yield_uncertainty_tha",
        "yield_source", "yield_blended_tha", "yield_source_blend"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
print(f"n features: {len(FEATS)}")

# ---------- F3 先行：缺失表 ----------
miss = df[FEATS].isna().sum()
miss = miss[miss > 0].sort_values(ascending=False)
miss_table = pd.DataFrame({"variable": miss.index, "n_missing": miss.values,
                           "pct": (miss.values / len(df) * 100).round(2)})
miss_table.to_csv(os.path.join(INT, "w15_f3_missing_table.csv"), index=False, encoding="utf-8-sig")
print("F3 missing cols:", miss_table.to_dict("records"))
# 18 格缺失的地理特征
if len(miss) > 0:
    miss_mask = df[miss.index[0]].isna()
    sub = df.loc[miss_mask, ["lon", "lat", "bio1", "soc_dgkg"]]
    print(f"F3: {miss_mask.sum()} grids missing terrain vars | bio1 mean={sub['bio1'].mean():.2f} vs rest {df.loc[~miss_mask,'bio1'].mean():.2f} | SOC mean={sub['soc_dgkg'].mean():.0f} vs rest {df.loc[~miss_mask,'soc_dgkg'].mean():.0f}")
    print("   lon range:", sub['lon'].min(), "-", sub['lon'].max(), "| lat range:", sub['lat'].min(), "-", sub['lat'].max())
    # 保存缺失格坐标供修复
    sub.to_csv(os.path.join(INT, "w15_f3_missing_grids.csv"), index=False, encoding="utf-8-sig")

# ---------- F2: PCA ----------
X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
sc = StandardScaler()
Xs = sc.fit_transform(X)
pca = PCA()
pcs = pca.fit_transform(Xs)
evr = pca.explained_variance_ratio_
cum = np.cumsum(evr)
n80 = int(np.argmax(cum >= 0.80) + 1)
print(f"F2: PC1 evr={evr[0]:.3f}, PC2={evr[1]:.3f}, n80={n80}")
# PC1 与 elevation 相关
elev = df["elevation_m"].values
mask = ~np.isnan(elev)
r_pc1_elev = np.corrcoef(pcs[mask, 0], elev[mask])[0, 1]
print(f"F2: corr(PC1, elevation) = {r_pc1_elev:.3f}")
# PC1-PC5 逐轴对 A / C 的单变量回归（43 格）
rows = []
for k in range(5):
    pc_k = pcs[:, k]
    if yA[m43].std() > 0:
        lr = LinearRegression().fit(pc_k[m43].reshape(-1, 1), yA[m43])
        r2_a = r2_score(yA[m43], lr.predict(pc_k[m43].reshape(-1, 1)))
    else:
        r2_a = np.nan
    rows.append({"PC": f"PC{k+1}", "evr": round(evr[k], 4), "r2_to_targetA_n43": round(r2_a, 4)})
# PC1-5 联合对 A
lr_all = LinearRegression().fit(pcs[m43, :5], yA[m43])
r2_all = r2_score(yA[m43], lr_all.predict(pcs[m43, :5]))
rows.append({"PC": "PC1-5_joint", "evr": round(cum[4], 4), "r2_to_targetA_n43": round(r2_all, 4)})
# PC1 对 C 目标（234 全体）
lr_c = LinearRegression().fit(pcs[:, 0].reshape(-1, 1), yC)
r2_c = r2_score(yC, lr_c.predict(pcs[:, 0].reshape(-1, 1)))
rows.append({"PC": "PC1_to_targetC", "evr": round(evr[0], 4), "r2_to_targetA_n43": round(r2_c, 4)})
pca_rows = pd.DataFrame(rows)
pca_rows.to_csv(os.path.join(INT, "w15_f2_pca.csv"), index=False, encoding="utf-8-sig")
print(pca_rows.to_string(index=False))
# 载荷 top（PC1 是什么）
load = pd.Series(pca.components_[0], index=FEATS).sort_values(key=abs, ascending=False)
json.dump({"pc1_evr": round(float(evr[0]), 4), "pc2_evr": round(float(evr[1]), 4),
           "n80": n80, "corr_pc1_elevation": round(float(r_pc1_elev), 4),
           "pc1_top_loadings": {k: round(v, 3) for k, v in load.head(8).items()},
           "pc12_evr_cum": round(float(cum[1]), 4)},
          open(os.path.join(INT, "w15_f2_pca_summary.json"), "w"), indent=1, ensure_ascii=False)

# ---------- F3b: KNN 插补版地形变量（供管线后续使用，非本轮替换主数据） ----------
imp = KNNImputer(n_neighbors=5, weights="distance")
terrain_cols = ["elevation_m", "slope_deg", "aspect_deg"]
have = [c for c in FEATS if c not in terrain_cols] + terrain_cols
Xi = imp.fit_transform(df[have].values)
df_imputed = df.copy()
for i, c in enumerate(terrain_cols):
    df_imputed[c] = Xi[:, -3 + i]
df_imputed.to_csv(os.path.join(INT, "data_with_yield_ensemble_terrain_imputed.csv"), index=False, encoding="utf-8-sig")
print("F3b: imputed terrain saved (KNN k=5, distance-weighted)")

# ---------- F4: GDD 基准温度反推 ----------
tavg_cols = [f"tavg_{m:02d}" for m in range(1, 13)]
gdd_cols = [f"GDD_{m:02d}" for m in range(1, 13)]
# 对每月：GDD = max(0, tavg - Tbase) 的期望 → 用多组 (tavg, GDD) 回归反推 Tbase
tt = df[tavg_cols].values.flatten()
gg = df[gdd_cols].values.flatten()
# 月度 GDD 定义应为 Σ daily max(0, tavg-Tbase) ≈ days_in_month * max(0, tavg_month - Tbase)
days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
days_arr = np.repeat(days, len(df)).astype(float)
active = gg > 0
if active.sum() > 100:
    # GDD/days vs tavg 的线性回归：GDD/days = tavg - Tbase（在正 GDD 域内）
    ratio = gg[active] / days_arr[active]
    lr = LinearRegression().fit(tt[active].reshape(-1, 1), ratio)
    tbase = -lr.intercept_ / lr.coef_[0] if lr.coef_[0] != 0 else np.nan
    r2 = r2_score(ratio, lr.predict(tt[active].reshape(-1, 1)))
    print(f"F4: inferred Tbase = {tbase:.2f} °C (R2={r2:.3f}, n_active={active.sum()})")
    # 零 GDD 月的 tavg 上界
    zero_months = tt[~active]
    print(f"F4: tmax of tavg in zero-GDD months = {zero_months.max():.2f} °C (should be <= Tbase)")
else:
    tbase, r2 = None, None
    print("F4: insufficient active months")
gdd_doc = {"inferred_Tbase_C": round(float(tbase), 2) if tbase is not None else None,
           "fit_r2": round(float(r2), 3) if r2 is not None else None,
           "GDD_gs_window_note": "GDD_gs 覆盖窗口与积温对象需对照生成脚本确认（pipeline_week2_3_rebuild.py）",
           "definition": "GDD_m = days_in_month * max(0, tavg_m - Tbase)（推断，待脚本核对）"}
json.dump(gdd_doc, open(os.path.join(INT, "w15_f4_gdd_doc.json"), "w"), indent=1, ensure_ascii=False)
print("W15 F2/F3/F4 done")
