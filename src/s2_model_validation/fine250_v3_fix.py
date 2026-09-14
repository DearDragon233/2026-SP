# -*- coding: utf-8 -*-
"""
W8-FIX: 月值 nodata 泄漏修复——过滤 nodata 后用 bio 变量插值替代
"""
import pandas as pd, numpy as np, os
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
df = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v2_enriched.csv"))

# 1) 找出 nodata 泄漏列（值域异常）
leak_cols = []
for c in df.columns:
    if df[c].dtype in ['float64', 'int64']:
        mn, mx = df[c].min(), df[c].max()
        if mn < -1e10 or mx > 1e10:
            leak_cols.append(c)
print("leaked columns:", leak_cols)
for c in leak_cols:
    valid = df[c][(df[c] > -1e10) & (df[c] < 1e10)]
    print(f"  {c}: valid={len(valid)}/{len(df)}, valid mean={valid.mean():.2f}")

# 2) 用该列的有效中位数填充 nodata
for c in leak_cols:
    valid_mask = (df[c] > -1e10) & (df[c] < 1e10)
    if valid_mask.sum() > 0:
        med = df.loc[valid_mask, c].median()
    else:
        med = 0
    df.loc[~valid_mask, c] = med
    print(f"  fixed {c}: nodata -> median {med:.2f}")

# 3) 重新计算衍生特征（基于清洁的月值）
ws = ["10","11","12","01","02","03","04","05","06"]
cm = ["06","07","08","09"]
tavg_ws_cols = [f"tavg_{m}" for m in ws]
df["gdd_ws"] = sum(df[c].clip(lower=0) for c in tavg_ws_cols)
df["prec_ws"] = sum(df[f"prec_{m}"] for m in ws)
df["prec_cm"] = sum(df[f"prec_{m}"] for m in cm)
df["tmin_jan"] = df["tavg_01"]
df["tmax_jul"] = df["tavg_07"]
prec_all = df[[f"prec_{i+1:02d}" for i in range(12)]].values
df["prec_cv"] = np.std(prec_all, axis=1) / np.mean(prec_all, axis=1)
df["tseason"] = df["tavg_07"] - df["tavg_01"]
df["aridity_ws"] = df["prec_ws"] / (df[[f"tavg_{m}" for m in ws]].mean(axis=1) + 10)

# 4) 清洁后最终特征集
exclude = ("lon", "lat", "cell_r", "cell_c", "yield_2021_tha", "n_px", "soil_class")
fc = [c for c in df.columns if c not in exclude and df[c].notna().sum() >= 100]
# 二次检查：去掉仍含 nodata 的列
for c in fc:
    if df[c].abs().max() > 1e10:
        print(f"  dropping {c} (still has nodata)")
        fc.remove(c)
print(f"clean features ({len(fc)}):", fc)

sc = StandardScaler(); X = sc.fit_transform(df[fc].values)
y = df["yield_2021_tha"].values

# 5) 用 Optuna 最优参数重跑
best_params = {'n_estimators': 428, 'max_depth': 5, 'learning_rate': 0.16843623145503986,
               'subsample': 0.5938179912547888, 'colsample_bytree': 0.8211225971512758,
               'min_child_weight': 6, 'reg_alpha': 3.5747246284730347, 'reg_lambda': 2.69406628416321}

models_final = {
    "XGBoost_tuned": XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0),
    "RF": RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    "Stacking": StackingRegressor(
        estimators=[
            ("xgb", XGBRegressor(**best_params, random_state=42, n_jobs=1, verbosity=0)),
            ("rf", RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1)),
        ], final_estimator=RidgeCV(cv=5)),
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
            f_r2.append(r2_score(y[te], p)); f_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
            yt[te] = y[te]; yp[te] = p
        r = {"Scheme": scheme, "Model": name, "R2_mean": round(np.mean(f_r2), 4),
             "R2_std": round(np.std(f_r2), 4), "RMSE_mean": round(np.mean(f_rmse), 4),
             "R2_pooled": round(r2_score(yt, yp), 4), "n": len(y)}
        results.append(r)
        print(f"  [{scheme:14s}] {name:14s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

res = pd.DataFrame(results)
res.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v3_results.csv"), index=False, encoding='utf-8-sig')

# 6) SHAP
try:
    import shap
    m = models_final["XGBoost_tuned"]; m.fit(X, y)
    expl = shap.TreeExplainer(m); sv = expl.shap_values(X)
    imp = np.abs(sv).mean(0)
    imp_df = pd.DataFrame({"feature": fc, "shap_mean_abs": np.round(imp, 4)}).sort_values(
        "shap_mean_abs", ascending=False)
    imp_df.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v3_shap.csv"), index=False)
    print("\nSHAP top 10 (clean):")
    print(imp_df.head(10).to_string())
except Exception as e:
    print("SHAP skip:", e)

df.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_v3_clean.csv"), index=False, encoding='utf-8-sig')
print("\nsaved: fine250_v3_results.csv, fine250_v3_shap.csv, fine250_v3_clean.csv")
