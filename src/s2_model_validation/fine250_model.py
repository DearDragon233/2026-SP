# -*- coding: utf-8 -*-
"""
W7-FINAL: 250m 建模管线（修复版特征 + Zenodo 301 格产量）
对比闫老师要求：大样本（301 vs 43）+ 正确方法（空间 CV + 随机 CV 对照）+ 可解释性（SHAP）
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
M = os.path.join(ROOT, "Outputs", "intermediate", "fine250_merged_fixed.csv")
df = pd.read_csv(M)
target = "yield_2021_tha"
exclude = ("lon", "lat", "cell_r", "cell_c", target, "n_px")
fc = [c for c in df.columns if c not in exclude and df[c].notna().sum() >= 100]
# nitrogen 全 NaN，剔除；其余 SoilGrids 部分缺失用中位数填充
for c in fc:
    if df[c].isna().sum() > 0:
        df[c] = df[c].fillna(df[c].median())
print(f"features ({len(fc)}):", fc)
print(f"n = {len(df)} | target: {target}")
print(f"  yield: {df[target].mean():.2f}±{df[target].std():.2f} t/ha")

X_raw = df[fc].values
sc = StandardScaler(); X = sc.fit_transform(X_raw)
y = df[target].values

def make_models():
    return {
        'XGBoost': XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbosity=0),
        'RF': RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    }

results = []
for scheme, n_folds in [("random_5fold", 5), ("spatial_4quadrant", 4)]:
    for name, mdl in make_models().items():
        if scheme == "random_5fold":
            kf = KFold(n_folds, shuffle=True, random_state=42)
            folds = list(kf.split(X))
        else:
            lat_med = np.median(df['lat']); lon_med = np.median(df['lon'])
            quad = (df['lat'] > lat_med).astype(int) * 2 + (df['lon'] > lon_med).astype(int)
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
        print(f"  [{scheme:20s}] {name:9s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

res = pd.DataFrame(results)
res.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_cv_final.csv"), index=False, encoding='utf-8-sig')

# SHAP
try:
    import shap
    m = make_models()['XGBoost']
    m.fit(X, y)
    expl = shap.TreeExplainer(m)
    sv = expl.shap_values(X)
    imp = np.abs(sv).mean(0)
    imp_df = pd.DataFrame({'feature': fc, 'shap_mean_abs': np.round(imp, 4)}).sort_values(
        'shap_mean_abs', ascending=False)
    imp_df.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_shap_final.csv"), index=False)
    print("\nSHAP top 8:")
    print(imp_df.head(8).to_string())
except Exception as e:
    print("SHAP skip:", e)

print("\nsaved fine250_cv_final.csv + fine250_shap_final.csv")
