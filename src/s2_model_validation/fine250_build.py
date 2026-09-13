# -*- coding: utf-8 -*-
"""
W7: 250m 细尺度重建 —— 响应闫老师反馈的系统性方案
====================================================
闫老师核心要求：① 消除过拟合（大样本）；② 让环境信号能被正确检测；
③ 方法框架可推广；④ 补充外部已发表数据验证。

方案：将分析尺度从 3.5km 网格（n=43/234）细化到 250m（n≈400-1500），
在 250m 尺度上重新提取环境特征（SRTM 30m→250m、SoilGrids 250m 原生、
WorldClim 2.5min≈5km→250m 双线性插值），Zenodo 30m 产量→250m 聚合（8×8）。

输出：
  Outputs/intermediate/fine250_features.csv      250m 网格环境特征矩阵
  Outputs/intermediate/fine250_yield.csv         250m 网格 Zenodo 产量
  Outputs/intermediate/fine250_merged.csv        合并建模表
  Outputs/figures/main/fig09_fine_scale_cv.png   细尺度 CV 结果
Author: Peng | 2026-09-13
"""
import rasterio, numpy as np, pandas as pd, os, warnings
warnings.filterwarnings("ignore")
from rasterio.windows import from_bounds
from rasterio.transform import rowcol
from rasterio.enums import Resampling
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
ZTIF = os.path.join(ROOT, "Data", "2021ChinaWheatYield30m.tif")
SRTM = os.path.join(ROOT, "Data", "SRTM", "srtm_60_04.tif")
SOIL_DIR = os.path.join(ROOT, "Data", "SoilGrids_wgs84")
WC_DIR = os.path.join(ROOT, "Data", "WorldClim")
OUT = os.path.join(ROOT, "Outputs", "intermediate")

# 平谷窗口
LON0, LON1, LAT0, LAT1 = 116.92, 117.24, 40.02, 40.22
# 250m 网格
CELL = 0.00225  # ~250m in deg

print("=" * 60)
print("W7: FINE-SCALE (250m) RECONSTRUCTION")
print("=" * 60)

# ---------- 1) Zenodo 产量 30m → 250m 聚合 ----------
with rasterio.open(ZTIF) as src:
    win = from_bounds(LON0, LAT0, LON1, LAT1, src.transform)
    arr = src.read(1, window=win)
    zt = src.window_transform(win)
valid = arr > 0
n_cells = int((LAT1 - LAT0) / CELL), int((LON1 - LON0) / CELL)
print(f"zenodo window: {arr.shape}, valid px: {valid.sum()} ({valid.mean()*100:.1f}%)")

rows_y = []
for r in range(n_cells[0]):
    for cc in range(n_cells[1]):
        la0 = LAT0 + r * CELL; lo0 = LON0 + cc * CELL
        r0, c0 = rowcol(zt, lo0, la0 + CELL)
        r1, c1 = rowcol(zt, lo0 + CELL, la0)
        r0, r1 = max(0, r0), min(arr.shape[0] - 1, r1)
        c0, c1 = max(0, c0), min(arr.shape[1] - 1, c1)
        if r1 <= r0 or c1 <= c0:
            continue
        sub = arr[r0:r1 + 1, c0:c1 + 1]
        msk = valid[r0:r1 + 1, c0:c1 + 1]
        n = msk.sum()
        if n >= 16:  # 至少 16/64 像元有效（25%覆盖）
            v = float(sub[msk].mean()) / 1000.0  # kg/ha → t/ha
            rows_y.append({"cell_r": r, "cell_c": cc,
                           "lon": lo0 + CELL / 2, "lat": la0 + CELL / 2,
                           "yield_2021_tha": round(v, 3), "n_px": n})
df_y = pd.DataFrame(rows_y)
print(f"[yield] 250m cells with valid yield: {len(df_y)}")
print(f"  range: {df_y['yield_2021_tha'].min():.2f}-{df_y['yield_2021_tha'].max():.2f} t/ha, "
      f"mean={df_y['yield_2021_tha'].mean():.2f}±{df_y['yield_2021_tha'].std():.2f}")
df_y.to_csv(os.path.join(OUT, "fine250_yield.csv"), index=False)

# ---------- 2) 环境特征提取到 250m 网格中心 ----------
centers = df_y[["lon", "lat"]].values
feat_dict = {"lon": centers[:, 0], "lat": centers[:, 1]}

def extract_center(tif_path, band=1, name=None):
    """读 250m 中心点值的稳健函数（支持不同 CRS/分辨率，用最近像元）"""
    name = name or os.path.basename(tif_path).replace(".tif", "")
    vals = []
    with rasterio.open(tif_path) as src:
        nod = src.nodata
        for la, lo in centers:
            try:
                r, c = rowcol(src.transform, lo, la)
                r = max(0, min(r, src.height - 1)); c = max(0, min(c, src.width - 1))
                v = src.read(band, window=rasterio.windows.Window(c, r, 1, 1))[0, 0]
                if nod is not None and v == nod: v = np.nan
                vals.append(float(v))
            except Exception:
                vals.append(np.nan)
    feat_dict[name] = vals
    nv = pd.Series(vals).dropna()
    print(f"  {name}: {len(nv)}/{len(vals)} valid, mean={nv.mean():.2f}")

print("\n[features] extracting to 250m centers...")
# SRTM 30m → elevation/slope（slope 简化：暂只取 elevation）
extract_center(SRTM, name="elevation_m")

# SoilGrids 250m（原生分辨率，8 个变量）
for f in os.listdir(SOIL_DIR):
    if f.endswith(".tif"):
        extract_center(os.path.join(SOIL_DIR, f), name=f.replace(".tif", ""))

# WorldClim 2.5min（~5km）→ 中心点双线性（近似：取最近像元）
# 选最有农学意义的：bio1(年均温) bio4(温度季节性) bio5(最热月max) bio12(年降水) bio15(降水季节性) GDD_gs(需计算)
for f in ["wc2.1_2.5m_bio_1.tif", "wc2.1_2.5m_bio_4.tif", "wc2.1_2.5m_bio_5.tif",
          "wc2.1_2.5m_bio_12.tif", "wc2.1_2.5m_bio_15.tif"]:
    extract_center(os.path.join(WC_DIR, f), name=f.replace("wc2.1_2.5m_", "").replace(".tif", ""))

# GDD：从 tavg 月值算（简化：只用 bio1 年均温做代理——正式版可读 12 个月计算）
# 这里用 WorldClim bio10(最暖季均温) 作为夏玉米生长季代理
extract_center(os.path.join(WC_DIR, "wc2.1_2.5m_bio_10.tif"), name="bio10_warmQ_mean")

df_feat = pd.DataFrame(feat_dict)
# 保留有意义的列
keep = ["lon", "lat", "elevation_m", "bdod_0-5cm_mean_5000", "cec_0-5cm_mean_5000",
        "clay_0-5cm_mean_5000", "nitrogen_0-5cm_mean_5000", "phh2o_0-5cm_mean_5000",
        "sand_0-5cm_mean_5000", "silt_0-5cm_mean_5000", "soc_0-5cm_mean_5000",
        "bio_1", "bio_4", "bio_5", "bio_12", "bio_15", "bio10_warmQ_mean"]
df_feat = df_feat[[k for k in keep if k in df_feat.columns]]
# 重命名简洁化
rename = {"bdod_0-5cm_mean_5000": "bdod", "cec_0-5cm_mean_5000": "cec",
          "clay_0-5cm_mean_5000": "clay", "nitrogen_0-5cm_mean_5000": "nitrogen",
          "phh2o_0-5cm_mean_5000": "ph", "sand_0-5cm_mean_5000": "sand",
          "silt_0-5cm_mean_5000": "silt", "soc_0-5cm_mean_5000": "soc",
          "bio_1": "bio1_tavg", "bio_4": "bio4_tseason", "bio_5": "bio5_tmax",
          "bio_12": "bio12_prec", "bio_15": "bio15_pseason", "bio10_warmQ_mean": "bio10_warmQ"}
df_feat = df_feat.rename(columns=rename)
print(f"[features] {df_feat.shape[1]-2} variables × {len(df_feat)} cells")

# ---------- 3) 合并 ----------
merged = df_y.merge(df_feat, on=["lon", "lat"], how="inner")
print(f"[merge] {len(merged)} cells with yield + features")
merged.to_csv(os.path.join(OUT, "fine250_merged.csv"), index=False)
print("saved fine250_merged.csv")

# ---------- 4) 建模：250m 尺度 CV ----------
print("\n[cv] fine-scale modeling (250m, n={})".format(len(merged)))
fc = [c for c in merged.columns if c not in ("lon", "lat", "cell_r", "cell_c", "yield_2021_tha", "n_px")]
X_raw = merged[fc].values
X = StandardScaler().fit_transform(X_raw)
y = merged["yield_2021_tha"].values

def make_models():
    return {
        'XGBoost': XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbosity=0),
        'RF': RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    }

results = []
for scheme, n_folds in [("random_5fold", 5), ("spatial_5fold", 5)]:
    for name, mdl in make_models().items():
        if scheme == "random_5fold":
            kf = KFold(n_folds, shuffle=True, random_state=42)
            folds = list(kf.split(X))
        else:
            # 空间折：按经纬度象限×中位数切 5 块
            lat_med = np.median(merged['lat']); lon_med = np.median(merged['lon'])
            quad = (merged['lat'] > lat_med).astype(int) * 2 + (merged['lon'] > lon_med).astype(int)
            folds = [(np.where(quad != q)[0], np.where(quad == q)[0]) for q in np.unique(quad)]
        f_r2, f_rmse = [], []
        yt_all, yp_all = np.zeros(len(y)), np.zeros(len(y))
        for tr, te in folds:
            if te.sum() < 10: continue
            m = mdl.__class__(**mdl.get_params())
            m.fit(X[tr], y[tr])
            p = m.predict(X[te])
            f_r2.append(r2_score(y[te], p))
            f_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
            yt_all[te] = y[te]; yp_all[te] = p
        r = {'Scheme': scheme, 'Model': name, 'R2_mean': round(np.mean(f_r2), 4),
             'R2_std': round(np.std(f_r2), 4), 'RMSE_mean': round(np.mean(f_rmse), 4),
             'R2_pooled': round(r2_score(yt_all, yp_all), 4), 'n': len(y)}
        results.append(r)
        print(f"  [{scheme}] {name:9s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

res = pd.DataFrame(results)
res.to_csv(os.path.join(OUT, "fine250_cv_results.csv"), index=False, encoding='utf-8-sig')
print("saved fine250_cv_results.csv")

# ---------- 5) SHAP 特征重要性（XGBoost random CV）----------
try:
    import shap
    m = make_models()['XGBoost']
    m.fit(X, y)
    expl = shap.TreeExplainer(m)
    sv = expl.shap_values(X)
    imp = np.abs(sv).mean(0)
    imp_df = pd.DataFrame({'feature': fc, 'shap_importance': np.round(imp, 4)}).sort_values(
        'shap_importance', ascending=False)
    imp_df.to_csv(os.path.join(OUT, "fine250_shap_importance.csv"), index=False)
    print("SHAP importance saved (top 5):")
    print(imp_df.head(5).to_string())
except Exception as e:
    print("SHAP skipped:", e)

print("\n" + "=" * 60)
print("W7 FINE-SCALE COMPLETE")
print("=" * 60)
