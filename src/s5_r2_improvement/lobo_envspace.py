# -*- coding: utf-8 -*-
"""外推增强实验（W10c）：
A. LOBO 8 块（地理外推强化版）：8 块 KMeans 坐标聚类，逐块留出
   对照 E0 / E5 / E8 / M0 —— E8 预期失效（负结果确认），M0 预期崩塌
B. 环境空间分块 vs 地理分块：按"预测产量空间"（E8 全模型 OOF 预测值 4 分位）
   与"特征空间"（58 环境 z-score kmeans 4 簇）分块，检验"环境外推"下
   E0/E5/E8 的表现——回答"混合模型该在何时退回纯环境模型"
C. 若 B 显示环境分块下 E0/E5 尚可：给出推荐操作边界（论文讨论用）
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
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
F2 = F0 + ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot",
           "ano_tmean", "ano_prec", "ano_gdd", "ano_t36", "ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
best_p = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
              colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
              random_state=42, n_jobs=2, verbosity=0)

def predict(feats, tr, te, topk=None, blend=False, idw=False):
    X = np.nan_to_num(v5[feats].values.astype(float), nan=0.0)
    sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
    if topk:
        m0 = XGBRegressor(**best_p); m0.fit(Xtr, y[tr])
        gain = m0.get_booster().get_score(importance_type="gain")
        idx = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])[:topk]
        keep = [i for i, _ in idx]
        Xtr, Xte = Xtr[:, keep], Xte[:, keep]
    m = XGBRegressor(**best_p); m.fit(Xtr, y[tr])
    pv = m.predict(Xte)
    if blend:
        rg = Ridge(alpha=1.0).fit(Xtr, y[tr])
        pv = 0.5 * pv + 0.5 * rg.predict(Xte)
    if idw:
        res_tr = y[tr] - m.predict(Xtr)
        cd = np.sqrt(((coords[te][:, None, :] - coords[tr][None, :, :]) ** 2).sum(-1))
        k = min(8, len(tr)); nn = np.argsort(cd, axis=1)[:, :k]
        w = 1.0 / np.maximum(cd[np.arange(len(te))[:, None], nn], 1e-3)
        pv = pv + (w * res_tr[nn]).sum(1) / w.sum(1)
    return pv

CFG = {"E0": dict(feats=F0), "E5": dict(feats=F2, topk=25),
       "E8": dict(feats=F2, idw=True), "M0": dict(feats=F0) and dict(feats=F0 + ["__lon__", "__lat__"])}

# M0 需要 lon/lat 进特征：包装一下
def predict_m0(tr, te):
    Xa = np.nan_to_num(v5[F0 + ["lon", "lat"]].values.astype(float), nan=0.0)
    sc = StandardScaler().fit(Xa[tr]); Xtr, Xte = sc.transform(Xa[tr]), sc.transform(Xa[te])
    m = XGBRegressor(**best_p); m.fit(Xtr, y[tr])
    return m.predict(Xte)

results = []
def lobo_eval(name, cfg, blocks):
    yt, yp = np.zeros(len(y)), np.zeros(len(y))
    for k in np.unique(blocks):
        te = np.where(blocks == k)[0]; tr = np.where(blocks != k)[0]
        if name == "M0":
            yp[te] = predict_m0(tr, te)
        else:
            yp[te] = predict(cfg["feats"], tr, te, topk=cfg.get("topk"),
                             blend=cfg.get("blend", False), idw=cfg.get("idw", False))
        yt[te] = y[te]
    r2 = r2_score(yt, yp)
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    print(f"{name}: pooled R2={r2:.4f} RMSE={rmse:.4f}")
    results.append({"scheme": SCHEME, "exp": name, "r2_pooled": round(r2, 4),
                    "rmse": round(rmse, 4), "mae": round(float(mean_absolute_error(yt, yp)), 4),
                    "n_blocks": int(len(np.unique(blocks)))})
    return yp

# ---------- A: LOBO 8 块 ----------
SCHEME = "LOBO_kmeans8_geo"
blocks8 = KMeans(8, random_state=42, n_init=10).fit_predict(coords)
print(f"--- A. LOBO 8 geo blocks (sizes {np.bincount(blocks8).tolist()}) ---")
for name, cfg in CFG.items():
    lobo_eval(name, cfg, blocks8)

# ---------- B: 环境空间分块 ----------
print("\n--- B1. blocks by E8 full-model OOF prediction quartiles (predicted-yield space) ---")
# E8 全模型 OOF 预测（从上轮 all_predictions_v3.csv 取）
pr = pd.read_csv(os.path.join(INT, "all_predictions_v3.csv"))
e8_oof = pr["E8_p"].values
SCHEME = "envspace_predq4"
pq4 = np.asarray(pd.qcut(e8_oof, 4, labels=False))
for name in ["E0", "E5", "E8"]:
    lobo_eval(name, CFG[name], pq4)

print("\n--- B2. blocks by 58-env z-score kmeans4 (feature space) ---")
SCHEME = "envspace_featk4"
Xf = np.nan_to_num(v5[F0].values.astype(float), nan=0.0)
Xf = StandardScaler().fit_transform(Xf)
fk4 = KMeans(4, random_state=42, n_init=10).fit_predict(Xf)
print(f"sizes {np.bincount(fk4).tolist()}")
for name in ["E0", "E5", "E8"]:
    lobo_eval(name, CFG[name], fk4)

res = pd.DataFrame(results)
res.to_csv(os.path.join(INT, "extrapolation_ledger.csv"), index=False, encoding="utf-8-sig")
print("\nsaved extrapolation_ledger.csv")
json.dump({"lobo8_sizes": np.bincount(blocks8).tolist(),
           "featk4_sizes": np.bincount(fk4).tolist(),
           "predq4_sizes": np.bincount(pq4).tolist()},
          open(os.path.join(INT, "extrapolation_blocks.json"), "w"), indent=1)
