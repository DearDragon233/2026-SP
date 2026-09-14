# -*- coding: utf-8 -*-
"""审稿响应实验包 W11b（诊断线 234 网格，对行动清单 #1/#2/#6/#8）：
A. 3 种子 CV 重复（四目标×三CV——复用既有折结构，重点补 C_blend 与 checker/lat_block 的 SD）
B. Split-conformal 校准 QRF 区间（行动 #2）
C. 目标 B 上界论证：Kriging/IDW 留一自检验 → 插值目标的信息上限（行动 #8）
D. 残差/产量 variogram 估计变程 → 块尺寸-变程比辩护棋盘 0.03°（行动 #6）
输出: Outputs/intermediate/review_response_diag_*.csv/json
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
SEEDS = [7, 21, 42]
drop = {"lon", "lat", "wheat_yield_tha", "yield_blended_tha"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
yC = df["yield_blended_tha"].values
yA_full = df["wheat_yield_tha"].values
print(f"234 grids, {len(FEATS)} features")

best = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
            colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
            random_state=42, n_jobs=2, verbosity=0)

def cv_run(y, scheme, seed, model="xgb"):
    X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
    n = len(y); yp = np.zeros(n)
    if scheme == "random":
        splits = list(KFold(5, shuffle=True, random_state=seed).split(X))
    elif scheme == "lat_block":
        latq = pd.qcut(coords[:, 1], 4, labels=False)
        splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
    else:  # checker_2d: 0.03° 棋盘
        gr = np.floor(coords[:, 0] / 0.03).astype(int) + np.floor(coords[:, 1] / 0.03).astype(int)
        ck = (gr % 2)
        splits = [(np.where(ck != k)[0], np.where(ck == k)[0]) for k in (0, 1)]
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        if model == "xgb":
            m = XGBRegressor(**{**best, "random_state": seed}); m.fit(Xtr, y[tr]); yp[te] = m.predict(Xte)
        else:
            m = RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=2); m.fit(Xtr, y[tr]); yp[te] = m.predict(Xte)
    return yp

# ---------- A: 3 种子（C_blend，XGB/RF×random/lat/checker） ----------
rows = []
for model, mname in [("xgb", "XGBoost"), ("rf", "RF")]:
    for scheme in ["random", "lat_block", "checker_2d"]:
        r2s, rs = [], []
        for s in SEEDS:
            yp = cv_run(yC, scheme, s, model)
            r2s.append(r2_score(yC, yp)); rs.append(np.sqrt(mean_squared_error(yC, yp)))
        rows.append({"Target": "C_blend_234", "Model": mname, "Scheme": scheme,
                     "R2_mean": round(np.mean(r2s), 4), "R2_std": round(np.std(r2s), 4),
                     "RMSE_mean": round(np.mean(rs), 4), "RMSE_std": round(np.std(rs), 4),
                     "r2_by_seed": [round(r, 4) for r in r2s]})
        print(f"A: {mname}/{scheme}: {np.mean(r2s):.4f}±{np.std(r2s):.4f}")
pd.DataFrame(rows).to_csv(os.path.join(INT, "review_response_diag_seeds.csv"), index=False, encoding="utf-8-sig")

# ---------- B: split-conformal 校准 QRF 区间 ----------
# QRF 用 RF 分位数（穷人版：RF 行内方差分位），校准用 split-conformal
from sklearn.model_selection import train_test_split
rest_idx, test_idx = train_test_split(np.arange(len(yC)), test_size=0.4, random_state=7)
tr_idx, cal_idx = train_test_split(rest_idx, test_size=0.5, random_state=7)  # 全体 30% train / 30% cal / 40% test
X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
sc = StandardScaler().fit(X[tr_idx])
rf = RandomForestRegressor(n_estimators=1000, random_state=7, n_jobs=2, oob_score=False)
rf.fit(sc.transform(X[tr_idx]), yC[tr_idx])
# 树间预测标准差作为初步区间宽度
all_pred = np.array([t.predict(sc.transform(X[test_idx])) for t in rf.estimators_])
q50 = all_pred.mean(0); spread = all_pred.std(0)
# 未校准区间: q50 ± 1.645*spread (名义90%)
lo_raw, hi_raw = q50 - 1.645 * spread, q50 + 1.645 * spread
# split-conformal：在校准集上求不合格分数
cal_pred = np.array([t.predict(sc.transform(X[cal_idx])) for t in rf.estimators_])
cal_q50 = cal_pred.mean(0); cal_spread = cal_pred.std(0)
scores = np.maximum((yC[cal_idx] - cal_q50) / (cal_spread + 1e-6), (cal_q50 - yC[cal_idx]) / (cal_spread + 1e-6))
qhat = np.quantile(scores, np.ceil((len(cal_idx) + 1) * 0.9) / len(cal_idx) - 1e-9)
lo_cf, hi_cf = q50 - qhat * (spread + 1e-6), q50 + qhat * (spread + 1e-6)
def picp(lo, hi): return float(np.mean((yC[test_idx] >= lo) & (yC[test_idx] <= hi)))
def mpw(lo, hi): return float(np.mean(hi - lo))
conf = {"n_train": int(len(tr_idx)), "n_cal": int(len(cal_idx)), "n_test": int(len(test_idx)),
        "qhat": round(float(qhat), 4),
        "raw": {"PICP_90": round(picp(lo_raw, hi_raw), 4), "MPW": round(mpw(lo_raw, hi_raw), 4)},
        "conformal": {"PICP_90": round(picp(lo_cf, hi_cf), 4), "MPW": round(mpw(lo_cf, hi_cf), 4)},
        "Q50_R2_test": round(r2_score(yC[test_idx], q50), 4)}
pd.DataFrame([{"variant": k, **v} for k, v in [("raw", conf["raw"]), ("conformal", conf["conformal"])]]).to_csv(
    os.path.join(INT, "review_response_conformal.csv"), index=False, encoding="utf-8-sig")
print("B: conformal:", json.dumps(conf))

# ---------- C: 目标 B 上界论证（IDW 留一自检验） ----------
from scipy.spatial import cKDTree
yb = df["yield_blended_tha"].values  # B 目标本质是空间插值产物
for k in [4, 8, 16]:
    tree = cKDTree(coords); n = len(yb)
    d, nn = tree.query(coords, k=k + 1)
    w = 1.0 / np.maximum(d[:, 1:], 1e-3)
    idw_pred = (w * yb[nn[:, 1:]]).sum(1) / w.sum(1)
    r2 = r2_score(yb, idw_pred)
    print(f"C: IDW self-test k={k}: R2={r2:.4f}")
    rows_c.append({"k": k, "idw_self_R2": round(r2, 4), "n": n}) if 'rows_c' in dir() else None
rows_c = []
for k in [4, 8, 16]:
    tree = cKDTree(coords); n = len(yb)
    d, nn = tree.query(coords, k=k + 1)
    w = 1.0 / np.maximum(d[:, 1:], 1e-3)
    idw_pred = (w * yb[nn[:, 1:]]).sum(1) / w.sum(1)
    rows_c.append({"k": k, "idw_self_R2": round(float(r2_score(yb, idw_pred)), 4), "n": n})
# 插值目标的产生参数（若有记录）：上界 = 1 - (插值误差方差)/(目标方差)
pd.DataFrame(rows_c).to_csv(os.path.join(INT, "review_response_targetB_bound.csv"), index=False, encoding="utf-8-sig")
print("C saved:", rows_c)

# ---------- D: variogram（产量与 C 目标 RF 残差） ----------
yp_rf = cv_run(yC, "random", 42, "rf")
res = yC - yp_rf
def emp_variogram(vals, max_lag=0.25, nbin=12):
    t = cKDTree(coords); pairs = t.query_pairs(r=max_lag, output_type='ndarray')
    d = np.sqrt(((coords[pairs[:, 0]] - coords[pairs[:, 1]]) ** 2).sum(1))
    g = 0.5 * (vals[pairs[:, 0]] - vals[pairs[:, 1]]) ** 2
    bins = np.linspace(0, max_lag, nbin + 1)
    out = []
    for i in range(nbin):
        m = (d >= bins[i]) & (d < bins[i + 1])
        if m.sum() > 10:
            out.append({"lag_km": round(float(d[m].mean() * 111), 2), "gamma": round(float(g[m].mean()), 5), "npairs": int(m.sum())})
    return out
vg_y = emp_variogram((yb - yb.mean()) / yb.std())
vg_r = emp_variogram(res / res.std())
sill_y = np.var(yb); 
# 变程估计：gamma 达到 0.95*sill 的首个 lag
def reach(vg, sill):
    for row in vg:
        if row["gamma"] >= 0.95 * sill:
            return row["lag_km"]
    return None
varinfo = {"yield_variogram": vg_y, "resid_variogram": vg_r,
           "note": "checker 块 0.03°≈3.3km；变程=gamma 首次达 0.95*sill 的 lag（km，经度度→km 近似×111）",
           "yield_reach_km": reach(vg_y, np.var((yb - yb.mean()) / yb.std() * yb.std())),
           "resid_reach_km": reach(vg_r, 1.0)}
json.dump(varinfo, open(os.path.join(INT, "review_response_variogram.json"), "w"), indent=1)
print("D: yield reach ~", varinfo["yield_reach_km"], "km; resid reach ~", varinfo["resid_reach_km"], "km; checker block = 3.3km")

json.dump({"conformal": conf, "targetB_bound": rows_c, "variogram": {"yield_reach_km": varinfo["yield_reach_km"], "resid_reach_km": varinfo["resid_reach_km"]}},
          open(os.path.join(INT, "review_response_diag_summary.json"), "w"), indent=1)
print("W11b done")
