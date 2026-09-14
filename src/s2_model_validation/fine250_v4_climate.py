# -*- coding: utf-8 -*-
"""月值数据修复：WorldClim 2.5min 分辨率太粗（~5km），平谷窗口可能只有 1-2 个像元
   所以 250m 中心点落在同一个低分辨率像元内 → 12 个月全为同一值或 nodata
   真正修复：不用 WorldClim 月值（分辨率不够），改用 bio 派生变量+已有 SoilGrids 变量
   或从 Zenodo 产量反向关联——但最正确的做法：用 3.5km 数据已有的月值列（prec_01..12, tavg_01..12），
   将其作为 250m 网格的气候背景（因为 5km WorldClim 在 3.5km 网格内几乎均匀）"""
import pandas as pd, numpy as np, os
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
# 用 3.5km 的月值数据（234 网格有完整的 prec_01..12 + tavg_01..12 + GDD_01..12）
df35 = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "data_with_yield_ensemble_full.csv"))
# 250m 的产量+环境
df250 = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_merged_fixed.csv"))

# 把 3.5km 的月值插值到 250m 网格（因为 WorldClim 2.5min 在此范围内几乎均匀，用 3.5km 的均值即可）
monthly_cols = [c for c in df35.columns if c.startswith(("prec_", "tavg_", "GDD_"))]
climate_mean = df35[monthly_cols].mean()  # 234 网格的平均值（空间不变量）
print("climate context (spatial mean):")
for c in monthly_cols[:6]:
    print(f"  {c}: {climate_mean[c]:.2f}")

# 将气候背景加到 250m 数据（作为全局常数——增加的排名信息有限，但补全了物理量）
for c in monthly_cols:
    df250[c] = climate_mean[c]

# 重新计算衍生特征（用正确的背景值）
ws = ["10","11","12","01","02","03","04","05","06"]
cm = ["06","07","08","09"]
df250["gdd_ws"] = sum(df250[f"GDD_{m}"] for m in ws)
df250["prec_ws"] = sum(df250[f"prec_{m}"] for m in ws)
df250["prec_cm"] = sum(df250[f"prec_{m}"] for m in cm)
df250["prec_cv"] = df250[[f"prec_{i+1:02d}" for i in range(12)]].values.std(axis=1) / df250[[f"prec_{i+1:02d}" for i in range(12)]].values.mean(axis=1)
df250["tseason"] = df250["tavg_07"] - df250["tavg_01"]
df250["aridity_ws"] = df250["prec_ws"] / (df250[[f"tavg_{m}" for m in ws]].mean(axis=1) + 10)

# 最终特征集
exclude = ("lon", "lat", "cell_r", "cell_c", "yield_2021_tha", "n_px", "soil_class")
fc = [c for c in df250.columns if c not in exclude and df250[c].notna().sum() >= 100]
for c in fc:
    if df250[c].isna().sum() > 0:
        df250[c] = df250[c].fillna(df250[c].median())
print(f"\nfeatures ({len(fc)}):", fc)

sc = StandardScaler(); X = sc.fit_transform(df250[fc].values)
y = df250["yield_2021_tha"].values

best_params = {'n_estimators': 428, 'max_depth': 5, 'learning_rate': 0.16843623145503986,
               'subsample': 0.5938179912547888, 'colsample_bytree': 0.8211225971512758,
               'min_child_weight': 6, 'reg_alpha': 3.5747246284730347, 'reg_lambda': 2.69406628416321}

models = {
    "XGBoost_tuned": XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0),
    "RF": RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    "Stacking": StackingRegressor(
        estimators=[("xgb", XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0)),
                    ("rf", RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1))],
        final_estimator=RidgeCV(cv=5)),
}

results = []
for scheme in ["random_5fold", "spatial_4quad"]:
    for name, mdl in models.items():
        if scheme == "random_5fold":
            kf = KFold(5, shuffle=True, random_state=42); folds = list(kf.split(X))
        else:
            lat_med = np.median(df250["lat"]); lon_med = np.median(df250["lon"])
            quad = (df250["lat"] > lat_med).astype(int) * 2 + (df250["lon"] > lon_med).astype(int)
            folds = [(np.where(quad != q)[0], np.where(quad == q)[0]) for q in np.unique(quad)]
        f_r2, f_rmse = [], []
        yt, yp = np.zeros(len(y)), np.zeros(len(y))
        for tr, te in folds:
            if te.sum() < 10: continue
            m = mdl.__class__(**mdl.get_params()) if name != "Stacking" else mdl
            m.fit(X[tr], y[tr]); p = m.predict(X[te])
            f_r2.append(r2_score(y[te], p)); f_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
            yt[te] = y[te]; yp[te] = p
        r = {"Scheme": scheme, "Model": name, "R2_mean": round(np.mean(f_r2), 4),
             "R2_std": round(np.std(f_r2), 4), "RMSE_mean": round(np.mean(f_rmse), 4),
             "R2_pooled": round(r2_score(yt, yp), 4), "n": len(y)}
        results.append(r)
        print(f"  [{scheme:14s}] {name:14s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

pd.DataFrame(results).to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v4_results.csv"), index=False, encoding='utf-8-sig')

try:
    import shap
    m = models["XGBoost_tuned"]; m.fit(X, y)
    sv = shap.TreeExplainer(m).shap_values(X)
    imp = pd.DataFrame({"feature": fc, "shap": np.round(np.abs(sv).mean(0), 4)}).sort_values("shap", ascending=False)
    imp.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v4_shap.csv"), index=False)
    print("\nSHAP top 10:")
    print(imp.head(10).to_string())
except Exception as e:
    print("SHAP skip:", e)

df250.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v4_final.csv"), index=False, encoding='utf-8-sig')
print("\nsaved: fine250_v4_results.csv, fine250_v4_shap.csv, fine250_v4_final.csv")
