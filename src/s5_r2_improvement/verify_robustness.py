# -*- coding: utf-8 -*-
"""稳健性检验包：
V1 重复 CV：E0/E5/E7/E8 × 5 种子随机 5 折（报告 mean±std，检验提升是否稳定）
V2 留出集：80/20（seed=7）一次性训练-评估 E0/E7/E8
V3 分块方式敏感性：纬度 4 块 / 经度 4 块 / 坐标 kmeans 4 块 × E0/E8
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
v5 = pd.read_csv(os.path.join(INT, "fine250_v5_features.csv"))
y = v5["yield_2021_tha"].values
coords = v5[["lon", "lat"]].values
F0 = [c for c in pd.read_csv(os.path.join(INT, "fine250_v4_final.csv")).columns
      if c not in ("cell_r", "cell_c", "lon", "lat", "yield_2021_tha", "n_px", "nitrogen")
      and pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))[c].dtype in ("float64", "int64")]
CLIM_ANO_IX = ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot",
               "ano_tmean", "ano_prec", "ano_gdd", "ano_t36", "ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
F2 = F0 + CLIM_ANO_IX
best_p = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
              colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
              random_state=42, n_jobs=2, verbosity=0)

def predict_model(feats, X_df, y_arr, tr, te, topk=None, blend=False, idw=False, seed=42):
    p = dict(best_p); p["random_state"] = seed
    X = np.nan_to_num(X_df[feats].values.astype(float), nan=0.0)
    sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
    if topk:
        m0 = XGBRegressor(**p); m0.fit(Xtr, y_arr[tr])
        gain = m0.get_booster().get_score(importance_type="gain")
        idx = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])[:topk]
        keep = [i for i, _ in idx]
        Xtr, Xte = Xtr[:, keep], Xte[:, keep]
    m = XGBRegressor(**p); m.fit(Xtr, y_arr[tr])
    pv = m.predict(Xte)
    if blend:
        rg = Ridge(alpha=1.0).fit(Xtr, y_arr[tr])
        pv = 0.5 * pv + 0.5 * rg.predict(Xte)
    if idw:
        res_tr = y_arr[tr] - m.predict(Xtr)
        cd = np.sqrt(((coords[te][:, None, :] - coords[tr][None, :, :]) ** 2).sum(-1))
        k = min(8, len(tr)); nn = np.argsort(cd, axis=1)[:, :k]
        w = 1.0 / np.maximum(cd[np.arange(len(te))[:, None], nn], 1e-3)
        pv = pv + (w * res_tr[nn]).sum(1) / w.sum(1)
    return pv

CFG = {"E0": dict(feats=F0), "E5": dict(feats=F2, topk=25),
       "E7": dict(feats=F2, topk=25, blend=True), "E8": dict(feats=F2, idw=True)}

# ---------- V1 重复 CV ----------
rows = []
for name, kw in CFG.items():
    r2s = []
    for seed in [42, 7, 123, 2026, 99]:
        kf = KFold(5, shuffle=True, random_state=seed)
        yt, yp = np.zeros(len(y)), np.zeros(len(y))
        for tr, te in kf.split(np.zeros(len(y))):
            yp[te] = predict_model(kw["feats"], v5, y, tr, te, topk=kw.get("topk"),
                                   blend=kw.get("blend", False), idw=kw.get("idw", False), seed=seed)
            yt[te] = y[te]
        r2s.append(r2_score(yt, yp))
    rows.append({"exp": name, "test": "repeated5x5", "r2_mean": round(np.mean(r2s), 4),
                 "r2_std": round(np.std(r2s), 4), "r2_min": round(min(r2s), 4), "r2_max": round(max(r2s), 4)})
    print(f"V1 {name}: {np.mean(r2s):.4f}±{np.std(r2s):.4f} (min {min(r2s):.4f})")

# ---------- V2 留出集 ----------
from sklearn.model_selection import train_test_split
idx_tr, idx_te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=7)
ho = []
for name, kw in CFG.items():
    pv = predict_model(kw["feats"], v5, y, idx_tr, idx_te, topk=kw.get("topk"),
                       blend=kw.get("blend", False), idw=kw.get("idw", False))
    r2 = r2_score(y[idx_te], pv)
    ho.append({"exp": name, "test": "holdout20", "r2": round(r2, 4),
               "rmse": round(float(np.sqrt(mean_squared_error(y[idx_te], pv))), 4),
               "mae": round(float(mean_absolute_error(y[idx_te], pv)), 4)})
    print(f"V2 {name}: holdout R2={r2:.4f}")

# ---------- V3 分块方式敏感性 ----------
from sklearn.cluster import KMeans
blocks = {
    "lat4": np.asarray(pd.qcut(coords[:, 1], 4, labels=False)),
    "lon4": np.asarray(pd.qcut(coords[:, 0], 4, labels=False)),
    "kmeans4": KMeans(4, random_state=42, n_init=10).fit_predict(coords),
}
v3rows = []
for bname, lab in blocks.items():
    for name in ["E0", "E8"]:
        kw = CFG[name]
        yt, yp = np.zeros(len(y)), np.zeros(len(y))
        for k in np.unique(lab):
            te = np.where(lab == k)[0]; tr = np.where(lab != k)[0]
            yp[te] = predict_model(kw["feats"], v5, y, tr, te, topk=kw.get("topk"),
                                   blend=kw.get("blend", False), idw=kw.get("idw", False))
            yt[te] = y[te]
        r2 = r2_score(yt, yp)
        v3rows.append({"block": bname, "exp": name, "spatial_r2": round(r2, 4)})
        print(f"V3 {bname} {name}: spatial R2={r2:.4f}")

pd.DataFrame(rows).to_csv(os.path.join(INT, "verify_repeated_cv.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(ho).to_csv(os.path.join(INT, "verify_holdout.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(v3rows).to_csv(os.path.join(INT, "verify_spatial_blocks.csv"), index=False, encoding="utf-8-sig")
json.dump({"repeated": rows, "holdout": ho, "spatial_blocks": v3rows},
          open(os.path.join(INT, "verification_package.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("verification package saved")
