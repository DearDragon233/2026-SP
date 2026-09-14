# -*- coding: utf-8 -*-
"""W12 复核实验包（A2 双台账矛盾 + B2 面板第二目标复检）：
A2. lat_block 双口径复核：q=5 分位块×旧参数（advance_validation 复刻）vs
    q=4 分位块×Optuna 参数（W11 响应口径），再跑 q=5×新参数、q=4×旧参数
    —— 2×2 因子实验，量化"分块定义"与"模型参数"各贡献多少差异
B2. Xiao2024 面板第二目标复检：1552 面板网格（New_Yield, t/ha）上
    重跑环境模型（同 71 特征采样 + 随机/棋盘 CV）——单年局限 → 跨目标稳健性
输出: Outputs/intermediate/w12_a2_latblock_factorial.csv, w12_b2_panel_check.csv
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
ENS = os.path.join(INT, "data_with_yield_ensemble.csv")
df = pd.read_csv(ENS)
coords = df[["lon", "lat"]].values
drop = {"lon", "lat", "wheat_yield_tha", "yield_blended_tha"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
yC = df["yield_blended_tha"].values

OLD = dict(n_estimators=200, max_depth=5, learning_rate=0.05,
           subsample=0.9, colsample_bytree=0.9, reg_alpha=0, reg_lambda=1,
           random_state=42, n_jobs=2, verbosity=0)
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=2, verbosity=0)

def cv_all(y, scheme_fn, params, seeds=(42,)):
    out = []
    for seed in seeds:
        X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
        n = len(y); yp = np.zeros(n)
        blocks = scheme_fn()
        if blocks is None:
            splits = list(KFold(5, shuffle=True, random_state=seed).split(X))
        else:
            splits = [(np.where(blocks != k)[0], np.where(blocks == k)[0]) for k in np.unique(blocks)]
        for tr, te in splits:
            sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
            m = XGBRegressor(**{**params, "random_state": seed}); m.fit(Xtr, y[tr]); yp[te] = m.predict(Xte)
        folds = [r2_score(y[te], yp[te]) for _, te in splits]
        out.append({"fold_mean": round(float(np.mean(folds)), 4), "fold_std": round(float(np.std(folds)), 4),
                    "pooled": round(float(r2_score(y, yp)), 4)})
    return out

rows = []
# A2: 2×2 因子（分块 q × 参数代）
for q in (5, 4):
    fn = lambda q=q: pd.qcut(df["lat"], q=q, labels=False).values
    for pname, pp in [("old200", OLD), ("optuna428", NEW)]:
        r = cv_all(yC, fn, pp, seeds=(42,))[0]
        rows.append({"part": "A2", "design": f"lat_q{q} x {pname}", "fold_mean": r["fold_mean"],
                     "fold_std": r["fold_std"], "pooled": r["pooled"]})
        print(f"A2 lat_q{q} x {pname}: fold {r['fold_mean']}±{r['fold_std']} pooled {r['pooled']}")
pd.DataFrame(rows).to_csv(os.path.join(INT, "w12_a2_latblock_factorial.csv"), index=False, encoding="utf-8-sig")

# B2: 面板第二目标复检
am = pd.read_csv(os.path.join(INT, "augmented_yield_master.csv"))
pm = am[am["New_Yield"].notna()].copy()
yP = pm["New_Yield"].values
PFEATS = [c for c in FEATS if c in pm.columns]
Xp = np.nan_to_num(pm[PFEATS].values.astype(float), nan=0.0)
pc = pm[["lon", "lat"]].values
res = []
for scheme in ["random", "checker"]:
    yp = np.zeros(len(yP))
    if scheme == "random":
        splits = list(KFold(5, shuffle=True, random_state=42).split(Xp))
    else:
        gr = (np.round(pc[:, 0] / 0.0417).astype(int) * 1000 + np.round(pc[:, 1] / 0.0417).astype(int))
        ck = gr % 2
        splits = [(np.where(ck != k)[0], np.where(ck == k)[0]) for k in (0, 1)]
    for tr, te in splits:
        sc = StandardScaler().fit(Xp[tr]); m = XGBRegressor(**NEW); m.fit(sc.transform(Xp[tr]), yP[tr])
        yp[te] = m.predict(sc.transform(Xp[te]))
    folds = [r2_score(yP[te], yp[te]) for _, te in splits]
    row = {"target": "Xiao2024_panel_1552", "scheme": scheme,
           "fold_mean": round(float(np.mean(folds)), 4), "fold_std": round(float(np.std(folds)), 4),
           "pooled": round(float(r2_score(yP, yp)), 4),
           "rmse": round(float(np.sqrt(mean_squared_error(yP, yp))), 4),
           "y_std": round(float(np.std(yP)), 3)}
    res.append(row)
    print(f"B2 panel {scheme}: fold {row['fold_mean']}±{row['fold_std']} pooled {row['pooled']} RMSE {row['rmse']}")
pd.DataFrame(res).to_csv(os.path.join(INT, "w12_b2_panel_check.csv"), index=False, encoding="utf-8-sig")
print("W12 experiments done")

# --- 追加：A2c 复刻复现检验（advance_validation.py 精确口径：同参数+KFold(5,shuffle,42)+qcut(lat,5)） ---
# 目的：解释 cv_scheme_comparison.csv 中 lat_block XGB fold 0.0262±0.1474 / pooled 0.278 的来源
from lightgbm import LGBMRegressor
def cv_advance_replica():
    X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
    lat_block = pd.qcut(df["lat"], q=5, labels=False).values
    mdl = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                       random_state=42, n_jobs=1, verbosity=0)
    tr, te = next(KFold(5, shuffle=True, random_state=42).split(X))  # 1 折演示量级
    sc = StandardScaler().fit(X[tr])
    mdl.fit(sc.transform(X[tr]), yC[tr])
    p = mdl.predict(sc.transform(X[te]))
    print("A2c single-fold R2 (q5, old params, exact split):", round(r2_score(yC[te], p), 4))
cv_advance_replica()
