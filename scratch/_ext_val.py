import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
z = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "zenodo_yield_2021_grid.csv"))
z_valid = z[z["zenodo_yield_tha"].notna()].copy()
print("Zenodo 2021 valid:", len(z_valid), "grids")

exclude = ("lon","lat","cell_r","cell_c","yield_2021_tha","n_px","zenodo_yield_tha",
           "yield_source","wheat_yield_pred_tha","wheat_yield_tha","yield_uncertainty_tha",
           "yield_blended_tha","yield_uncertainty_blend","yield_source_blend")
# 只保留数值列
feat = []
for c in z_valid.columns:
    if c in exclude: continue
    if z_valid[c].dtype in ["float64", "int64"] and z_valid[c].notna().sum() >= 5:
        feat.append(c)
print("numeric features:", feat)

for c in feat:
    z_valid[c] = z_valid[c].fillna(z_valid[c].median())

sc = StandardScaler(); Xz = sc.fit_transform(z_valid[feat].values)
y_z = z_valid["zenodo_yield_tha"].values

def make_models():
    return {
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbosity=0),
        "RF": RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
    }

rows = []
for scheme, n_folds in [("random_5fold", 5), ("checker_4fold", 4)]:
    if scheme == "random_5fold":
        kf = KFold(n_folds, shuffle=True, random_state=42); folds = list(kf.split(Xz))
    else:
        lat_med = np.median(z_valid["lat"]); lon_med = np.median(z_valid["lon"])
        quad = (z_valid["lat"] > lat_med).astype(int) * 2 + (z_valid["lon"] > lon_med).astype(int)
        folds = [(np.where(quad != q)[0], np.where(quad == q)[0]) for q in np.unique(quad)]
    for name, mdl in make_models().items():
        f_r2, f_rmse = [], []
        yt, yp = np.zeros(len(y_z)), np.zeros(len(y_z))
        for tr, te in folds:
            if te.sum() < 5: continue
            m = mdl.__class__(**mdl.get_params())
            m.fit(Xz[tr], y_z[tr]); p = m.predict(Xz[te])
            f_r2.append(r2_score(y_z[te], p)); f_rmse.append(np.sqrt(mean_squared_error(y_z[te], p)))
            yt[te] = y_z[te]; yp[te] = p
        r = {"Experiment": "external_zenodo_2021", "Scheme": scheme, "Model": name,
             "R2_mean": round(np.mean(f_r2), 4), "R2_std": round(np.std(f_r2), 4),
             "RMSE_mean": round(np.mean(f_rmse), 4),
             "R2_pooled": round(r2_score(yt, yp), 4), "n": len(y_z)}
        rows.append(r)
        print(f"  [{scheme}] {name}: R2={r['R2_mean']:.4f} pooled={r['R2_pooled']:.4f}")

res = pd.DataFrame(rows)
res.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "external_validation_results.csv"), index=False, encoding="utf-8-sig")
print("saved external_validation_results.csv")
