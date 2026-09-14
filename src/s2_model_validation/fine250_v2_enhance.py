# -*- coding: utf-8 -*-
"""
W8: 模型性能提升
=================
1. 特征工程：
   - GDD 逐月累积（生长季积温，冬小麦 10-6 月）
   - 温度极值（Tmax_max, Tmin_min 冬季低温）
   - 降水集中度（CV）
   - 地形衍生（elevation 与 slope 的交互——坡地对产量影响不同）
   - 土壤衍生（clay*soc 交互、SPAC 分类编码）
2. 超参数优化：Optuna 搜索 XGBoost/LightGBM 最优参数
3. 模型融合：Stacking（XGB+RF+LightGBM → Ridge 元学习器）
4. 最终 CV 验证 + 性能对比表
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
M = os.path.join(ROOT, "Outputs", "intermediate", "fine250_merged_fixed.csv")
df = pd.read_csv(M)

# WorldClim 月值（tavg_01..12, prec_01..12）在 3.5km 数据里，不在 250m 数据里
# 250m 只有 bio1/4/5/10/12/15。需要从 WorldClim 栅格提取月值到 250m 中心。
# 先检查月值 tif 是否存在
wc_dir = os.path.join(ROOT, "Data", "WorldClim")
tavg_files = sorted([f for f in os.listdir(wc_dir) if f.startswith("wc2.1_2.5m_tavg_")])
prec_files = sorted([f for f in os.listdir(wc_dir) if f.startswith("wc2.1_2.5m_prec_")])
print(f"tavg files: {len(tavg_files)}, prec files: {len(prec_files)}")

# 提取月值到 250m 中心
import rasterio
from rasterio.windows import Window
from pyproj import Transformer

centers = df[["lon", "lat"]].values

def extract_monthly(file_list, prefix):
    """提取逐月栅格值到 250m 中心"""
    tr_4326 = Transformer.from_crs("EPSG:4326", "EPSG:4326", always_xy=True)
    monthly = {}
    for f in file_list:
        month = f.replace(prefix, "").replace(".tif", "")
        with rasterio.open(os.path.join(wc_dir, f)) as src:
            vals = []
            for la, lo in centers:
                r, c = rasterio.transform.rowcol(src.transform, lo, la)
                r = max(0, min(r, src.height-1)); c = max(0, min(c, src.width-1))
                v = float(src.read(1, window=Window(c, r, 1, 1))[0,0])
                vals.append(v)
        monthly[month] = vals
    return monthly

print("extracting monthly tavg...")
tavg = extract_monthly(tavg_files, "wc2.1_2.5m_tavg_")
print("extracting monthly prec...")
prec = extract_monthly(prec_files, "wc2.1_2.5m_prec_")

tavg_df = pd.DataFrame(tavg); prec_df = pd.DataFrame(prec)
# 重命名列：tavg_01..12, prec_01..12
tavg_df.columns = [f"tavg_{i+1:02d}" for i in range(12)]
prec_df.columns = [f"prec_{i+1:02d}" for i in range(12)]
# 对齐索引
for c in tavg_df.columns: df[c] = tavg_df[c].values
for c in prec_df.columns: df[c] = prec_df[c].values

# ============ 特征工程 ============
# 冬小麦生长季（10月播种→次年6月收获）：10,11,12,1,2,3,4,5,6
ws_months = ["10","11","12","01","02","03","04","05","06"]
# 夏玉米生长季（6月→9月）：06,07,08,09
cm_months = ["06","07","08","09"]

# 生长季积温（GDD base 0°C，冬小麦）
tavg_ws_cols = [f"tavg_{m}" for m in ws_months]
df["gdd_ws"] = sum(max(0, df[c].mean()) for c in tavg_ws_cols)  # 简化：月均温>0 的累加
df["gdd_ws"] = sum(df[c].clip(lower=0) for c in tavg_ws_cols)

# 生长季降水
df["prec_ws"] = sum(df[f"prec_{m}"] for m in ws_months)
df["prec_cm"] = sum(df[f"prec_{m}"] for m in cm_months)

# 冬季低温（1月均温，冻害代理）
df["tmin_jan"] = df["tavg_01"]
# 夏季高温（7月均温，热胁迫代理）
df["tmax_jul"] = df["tavg_07"]
# 降水季节性（CV of monthly precip）
prec_all = df[[f"prec_{i+1:02d}" for i in range(12)]].values
df["prec_cv"] = np.std(prec_all, axis=1) / np.mean(prec_all, axis=1)
# 温度年较差
df["tseason"] = df["tavg_07"] - df["tavg_01"]
# 干湿比（生长季降水/潜在蒸散代理 = prec_ws / (tavg_ws+10)）
df["aridity_ws"] = df["prec_ws"] / (df[[f"tavg_{m}" for m in ws_months]].mean(axis=1) + 10)
# 地形×土壤交互
df["elev_clay"] = df["elevation_m"] * df["clay"] / 1000
df["soc_ph"] = df["soc"] * df["phh2o"] / 100
# 土壤质地分类（clay>30% = clayey, sand>60% = sandy, else loam）
df["soil_class"] = pd.cut(df["clay"], bins=[0, 20, 35, 100], labels=[0, 1, 2]).astype(float)

new_feats = ["gdd_ws", "prec_ws", "prec_cm", "tmin_jan", "tmax_jul", "prec_cv",
             "tseason", "aridity_ws", "elev_clay", "soc_ph", "soil_class"]
print(f"\nnew features: {new_feats}")
for c in new_feats:
    print(f"  {c}: mean={df[c].mean():.2f}, std={df[c].std():.2f}")

# ============ 最终特征集 ============
exclude = ("lon", "lat", "cell_r", "cell_c", "yield_2021_tha", "n_px", "soil_class")
fc_all = [c for c in df.columns if c not in exclude and df[c].notna().sum() >= 100]
print(f"\ntotal features: {len(fc_all)}")

# 填充缺失
for c in fc_all:
    if df[c].isna().sum() > 0:
        df[c] = df[c].fillna(df[c].median())

X_raw = df[fc_all].values
sc = StandardScaler(); X = sc.fit_transform(X_raw)
y = df["yield_2021_tha"].values

# ============ Optuna 超参数优化 ============
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 600),
            "max_depth": trial.suggest_int("max_depth", 3, 9),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.5, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 5),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 5),
        }
        m = XGBRegressor(**params, random_state=42, n_jobs=1, verbosity=0)
        kf = KFold(5, shuffle=True, random_state=42)
        scores = []
        for tr, te in kf.split(X):
            m.fit(X[tr], y[tr]); p = m.predict(X[te])
            scores.append(r2_score(y[te], p))
        return np.mean(scores)
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=50, show_progress_bar=False)
    best_params = study.best_params
    print(f"\nOptuna best R²={study.best_value:.4f}")
    print(f"best params: {best_params}")
except ImportError:
    print("optuna not installed, skipping HP tuning")
    best_params = {"n_estimators": 300, "max_depth": 5, "learning_rate": 0.05,
                   "subsample": 0.8, "colsample_bytree": 0.8}

# ============ 最终模型对比 ============
print("\n=== FINAL MODEL COMPARISON ===")
models_final = {
    "XGBoost_tuned": XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0),
    "RF": RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    "Stacking": StackingRegressor(
        estimators=[
            ("xgb", XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0)),
            ("rf", RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1)),
        ],
        final_estimator=RidgeCV(cv=5)),
}

results = []
for scheme, n_folds in [("random_5fold", 5), ("spatial_4quad", 4)]:
    for name, mdl in models_final.items():
        if scheme == "random_5fold":
            kf = KFold(n_folds, shuffle=True, random_state=42)
            folds = list(kf.split(X))
        else:
            lat_med = np.median(df["lat"]); lon_med = np.median(df["lon"])
            quad = (df["lat"] > lat_med).astype(int) * 2 + (df["lon"] > lon_med).astype(int)
            folds = [(np.where(quad != q)[0], np.where(quad == q)[0]) for q in np.unique(quad)]
        f_r2, f_rmse = [], []
        yt, yp = np.zeros(len(y)), np.zeros(len(y))
        for tr, te in folds:
            if te.sum() < 10: continue
            m = mdl.__class__(**mdl.get_params()) if name != "Stacking" else mdl
            m.fit(X[tr], y[tr]); p = m.predict(X[te])
            f_r2.append(r2_score(y[te], p))
            f_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
            yt[te] = y[te]; yp[te] = p
        r = {"Scheme": scheme, "Model": name, "R2_mean": round(np.mean(f_r2), 4),
             "R2_std": round(np.std(f_r2), 4), "RMSE_mean": round(np.mean(f_rmse), 4),
             "R2_pooled": round(r2_score(yt, yp), 4), "n": len(y)}
        results.append(r)
        print(f"  [{scheme:14s}] {name:14s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

res = pd.DataFrame(results)
res.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v2_results.csv"), index=False, encoding='utf-8-sig')

# SHAP
try:
    import shap
    m = models_final["XGBoost_tuned"]
    m.fit(X, y)
    expl = shap.TreeExplainer(m)
    sv = expl.shap_values(X)
    imp = np.abs(sv).mean(0)
    imp_df = pd.DataFrame({"feature": fc_all, "shap_mean_abs": np.round(imp, 4)}).sort_values(
        "shap_mean_abs", ascending=False)
    imp_df.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v2_shap.csv"), index=False)
    print("\nSHAP top 10:")
    print(imp_df.head(10).to_string())
except Exception as e:
    print("SHAP skip:", e)

# 保存最终数据
df.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v2_enriched.csv"), index=False, encoding='utf-8-sig')
print("\nsaved: fine250_v2_results.csv, fine250_v2_shap.csv, fine250_v2_enriched.csv")
