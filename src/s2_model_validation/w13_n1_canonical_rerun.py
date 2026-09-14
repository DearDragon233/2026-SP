# -*- coding: utf-8 -*-
"""W13-N1: 权威配置（q4 lat 块 × Optuna 参数 × C_blend）3 种子重跑，
同时产出 pooled 与 fold 双口径，重写权威台账为显式列版本。
同时重生成 cv_optimism_gap.csv（pooled+fold 双列，N3）。
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
df = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble.csv"))
coords = df[["lon", "lat"]].values
drop = {"lon", "lat", "wheat_yield_tha", "yield_blended_tha"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
yC = df["yield_blended_tha"].values
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=2, verbosity=0)

def cv_scheme(scheme, seed):
    X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
    n = len(yC); yp = np.zeros(n)
    if scheme == "random":
        splits = list(KFold(5, shuffle=True, random_state=seed).split(X))
    elif scheme == "lat4":
        latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
        splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
    else:  # checker_2d 0.03deg
        gr = np.floor((coords[:, 0] - coords[:, 0].min()) / 0.03).astype(int) * 100 + \
             np.floor((coords[:, 1] - coords[:, 1].min()) / 0.03).astype(int)
        ck = gr % 2
        splits = [(np.where(ck != k)[0], np.where(ck == k)[0]) for k in (0, 1)]
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        m = XGBRegressor(**{**NEW, "random_state": seed}); m.fit(Xtr, yC[tr]); yp[te] = m.predict(Xte)
    folds = [r2_score(yC[te], yp[te]) for _, te in splits]
    return {"pooled": r2_score(yC, yp), "fold_mean": float(np.mean(folds)), "fold_std": float(np.std(folds)),
            "rmse": float(np.sqrt(mean_squared_error(yC, yp)))}

XGB, RF = "XGBoost", "RF"
from sklearn.ensemble import RandomForestRegressor
def cv_scheme_rf(scheme, seed):
    X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
    n = len(yC); yp = np.zeros(n)
    if scheme == "random":
        splits = list(KFold(5, shuffle=True, random_state=seed).split(X))
    elif scheme == "lat4":
        latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
        splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
    else:
        gr = np.floor((coords[:, 0] - coords[:, 0].min()) / 0.03).astype(int) * 100 + \
             np.floor((coords[:, 1] - coords[:, 1].min()) / 0.03).astype(int)
        ck = gr % 2
        splits = [(np.where(ck != k)[0], np.where(ck == k)[0]) for k in (0, 1)]
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr])
        m = RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=2)
        m.fit(sc.transform(X[tr]), yC[tr]); yp[te] = m.predict(sc.transform(X[te]))
    folds = [r2_score(yC[te], yp[te]) for _, te in splits]
    return {"pooled": r2_score(yC, yp), "fold_mean": float(np.mean(folds)), "fold_std": float(np.std(folds)),
            "rmse": float(np.sqrt(mean_squared_error(yC, yp)))}

rows = []
for model, fn in [(XGB, cv_scheme), (RF, cv_scheme_rf)]:
    for scheme in ["random", "lat4", "checker_2d"]:
        rs = [fn(scheme, s) for s in SEEDS]
        rows.append({
            "Target": "C_blend_234", "Model": model, "Scheme": scheme,
            "pooled_mean": round(float(np.mean([r["pooled"] for r in rs])), 4),
            "pooled_std": round(float(np.std([r["pooled"] for r in rs])), 4),
            "pooled_by_seed": [round(r["pooled"], 4) for r in rs],
            "fold_mean_mean": round(float(np.mean([r["fold_mean"] for r in rs])), 4),
            "fold_mean_std": round(float(np.std([r["fold_mean"] for r in rs])), 4),
            "fold_by_seed": [[round(r["fold_mean"], 4), round(r["fold_std"], 4)] for r in rs],
            "RMSE_mean": round(float(np.mean([r["rmse"] for r in rs])), 4),
            "n_seeds": 3, "seeds": SEEDS,
            "params": "optuna428 (428/5/0.168/0.594/0.821/mcw6/a3.57/l2.69)" if model == XGB else "RF500",
        })
        print(f"{model}/{scheme}: pooled {rows[-1]['pooled_mean']}±{rows[-1]['pooled_std']} fold {rows[-1]['fold_mean_mean']}±{rows[-1]['fold_mean_std']}")
out = pd.DataFrame(rows)
out.to_csv(os.path.join(INT, "review_response_diag_seeds_v2.csv"), index=False, encoding="utf-8-sig")

# N3: cv_optimism_gap.csv 重生成（pooled 主 + fold 辅）
g = []
for model in [XGB, RF]:
    pr = out[(out.Model == model) & (out.Scheme == "random")].iloc[0]
    for scheme, label in [("lat4", "lat_block"), ("checker_2d", "checker_2d")]:
        sp = out[(out.Model == model) & (out.Scheme == scheme)].iloc[0]
        g.append({"Model": model, "SpatialScheme": label,
                  "pooled_gap": round(pr["pooled_mean"] - sp["pooled_mean"], 4),
                  "pooled_gap_by_seed": [round(a - b, 4) for a, b in zip(pr["pooled_by_seed"], sp["pooled_by_seed"])],
                  "fold_gap": round(pr["fold_mean_mean"] - sp["fold_mean_mean"], 4),
                  "note": "pooled primary / fold secondary"})
pd.DataFrame(g).to_csv(os.path.join(INT, "cv_optimism_gap.csv"), index=False, encoding="utf-8-sig")
print("gap regenerated:", g[0]["pooled_gap"], g[1]["pooled_gap"], "| fold:", g[0]["fold_gap"], g[1]["fold_gap"])
print("W13-N1 done")
