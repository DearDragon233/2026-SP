# -*- coding: utf-8 -*-
"""独立复现脚本：验证 external_validation_results.csv 的数字可重现。
与 _ext_val.py 相同的种子(42)与参数，不同文件名与输出路径。
预期：R2 与首次运行完全一致（同种子同参数 → 确定性）。"""
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

exclude = ("lon","lat","cell_r","cell_c","yield_2021_tha","n_px","zenodo_yield_tha",
           "yield_source","wheat_yield_pred_tha","wheat_yield_tha","yield_uncertainty_tha",
           "yield_blended_tha","yield_uncertainty_blend","yield_source_blend")
feat = [c for c in z_valid.columns
        if c not in exclude and z_valid[c].dtype in ["float64","int64"]
        and z_valid[c].notna().sum() >= 5]
for c in feat:
    z_valid[c] = z_valid[c].fillna(z_valid[c].median())

sc = StandardScaler(); Xz = sc.fit_transform(z_valid[feat].values)
y = z_valid["zenodo_yield_tha"].values

models = {
    "XGBoost": lambda: XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                                    subsample=0.8, colsample_bytree=0.8, random_state=42,
                                    n_jobs=1, verbosity=0),
    "RF": lambda: RandomForestRegressor(n_estimators=300, max_depth=9, random_state=42, n_jobs=1),
}

out = []
for scheme in ["random_5fold", "checker_4fold"]:
    if scheme == "random_5fold":
        folds = list(KFold(5, shuffle=True, random_state=42).split(Xz))
    else:
        lm, om = np.median(z_valid["lat"]), np.median(z_valid["lon"])
        q = (z_valid["lat"] > lm).astype(int)*2 + (z_valid["lon"] > om).astype(int)
        folds = [(np.where(q != k)[0], np.where(q == k)[0]) for k in np.unique(q)]
    for name, mk in models.items():
        yt, yp = np.zeros(len(y)), np.zeros(len(y))
        for tr, te in folds:
            if te.sum() < 5: continue
            m = mk(); m.fit(Xz[tr], y[tr]); yp[te] = m.predict(Xz[te]); yt[te] = y[te]
        out.append({"Scheme": scheme, "Model": name,
                    "R2_pooled_repro": round(r2_score(yt, yp), 4)})

rep = pd.DataFrame(out)
first = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "external_validation_results.csv"))
first_map = {(r["Scheme"], r["Model"]): r["R2_pooled"] for _, r in first.iterrows()}
rep["R2_pooled_first"] = [first_map[(r["Scheme"], r["Model"])] for _, r in rep.iterrows()]
rep["match"] = rep["R2_pooled_repro"] == rep["R2_pooled_first"]
print(rep.to_string(index=False))
print("\nREPRODUCTION:", "ALL MATCH" if rep["match"].all() else "MISMATCH FOUND")
rep.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "external_validation_repro_check.csv"),
           index=False, encoding="utf-8-sig")
