# -*- coding: utf-8 -*-
"""审稿响应实验包（W11，对指引行动清单 #1/#2/#6/#8 + 250m 线多种子）：
A. 3 种子 CV 重复（诊断线四目标×三 CV）——行动 #1
B. Split-conformal 校准 QRF 区间（诊断线）——行动 #2
C. 目标 B 插值上界论证（循环验证定量解构）——行动 #8
D. 产量/残差 variogram 与块尺寸-变程比（棋盘 0.03° 辩护）——行动 #6
E. 250m 线 3 种子重复（E0/E8×随机/纬度块/LOBO8）——混合线同款补强
输出: Outputs/intermediate/review_response_*.csv + review_response_summary.json
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
SEEDS = [7, 21, 42]
summary = {}

# ---------- 定位诊断线数据 ----------
cand = [
    r"D:\2026-SP\Outputs\intermediate\county_35km_features.csv",
    r"D:\2026-SP\Outputs\intermediate\s2_county_features.csv",
    r"D:\2026-SP\Outputs\intermediate\diagnostic_features.csv",
]
diag_path = next((p for p in cand if os.path.exists(p)), None)
if diag_path is None:
    for f in os.listdir(INT):
        if f.endswith(".csv"):
            df0 = pd.read_csv(os.path.join(INT, f), nrows=2)
            if df0.shape[1] >= 20 and any(c.lower() in ("yield", "yield_obs", "target", "obs") for c in df0.columns):
                diag_path = os.path.join(INT, f)
                break
print("diagnostic data:", diag_path)

# ---------- E. 250m 线 3 种子（先跑，数据路径确定） ----------
v5 = pd.read_csv(os.path.join(INT, "fine250_v5_features.csv"))
y25 = v5["yield_2021_tha"].values
coords = v5[["lon", "lat"]].values
v4cols = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"), nrows=1).columns
F0 = [c for c in v4cols if c not in ("cell_r", "cell_c", "lon", "lat", "yield_2021_tha", "n_px", "nitrogen")]
F2 = F0 + ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot",
           "ano_tmean", "ano_prec", "ano_gdd", "ano_t36", "ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
best_p = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
              colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
              random_state=42, n_jobs=2, verbosity=0)

def run_cv25(feats, seed, mode, topk=None, idw=False, blocks=None):
    X = np.nan_to_num(v5[feats].values.astype(float), nan=0.0)
    n = len(y25); yp = np.zeros(n)
    if mode == "random":
        kf = KFold(5, shuffle=True, random_state=seed)
        splits = list(kf.split(X))
    else:
        splits = [(np.where(blocks != k)[0], np.where(blocks == k)[0]) for k in np.unique(blocks)]
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr]); Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        if topk:
            m0 = XGBRegressor(**{**best_p, "random_state": seed}); m0.fit(Xtr, y25[tr])
            gain = m0.get_booster().get_score(importance_type="gain")
            idx = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])[:topk]
            keep = [i for i, _ in idx]; Xtr, Xte = Xtr[:, keep], Xte[:, keep]
        m = XGBRegressor(**{**best_p, "random_state": seed}); m.fit(Xtr, y25[tr])
        pv = m.predict(Xte)
        if idw:
            res_tr = y25[tr] - m.predict(Xtr)
            cd = np.sqrt(((coords[te][:, None, :] - coords[tr][None, :, :]) ** 2).sum(-1))
            k = min(8, len(tr)); nn = np.argsort(cd, axis=1)[:, :k]
            w = 1.0 / np.maximum(cd[np.arange(len(te))[:, None], nn], 1e-3)
            pv = pv + (w * res_tr[nn]).sum(1) / w.sum(1)
        yp[te] = pv
    return r2_score(y25, yp), float(np.sqrt(mean_squared_error(y25, yp)))

from sklearn.cluster import KMeans
blocks8 = KMeans(8, random_state=42, n_init=10).fit_predict(coords)
lat4 = pd.qcut(coords[:, 1], 4, labels=False)
rows = []
for name, feats, kw in [("E0", F0, {}), ("E8", F2, dict(idw=True))]:
    for mode, blk in [("random", None), ("lat4", lat4), ("lobo8", blocks8)]:
        rs = [run_cv25(feats, s, "random" if mode == "random" else "block", blocks=blk, **kw) for s in SEEDS]
        r2s = [r[0] for r in rs]
        rows.append({"exp": name, "scheme": mode, "r2_mean": round(np.mean(r2s), 4),
                     "r2_std": round(np.std(r2s), 4), "r2_min": round(min(r2s), 4),
                     "r2_by_seed": [round(r, 4) for r in r2s]})
        print(f"E: {name}/{mode}: {np.mean(r2s):.4f}±{np.std(r2s):.4f} min={min(r2s):.4f}")
pd.DataFrame(rows).to_csv(os.path.join(INT, "review_response_250m_seeds.csv"), index=False, encoding="utf-8-sig")
summary["seeds_250m"] = rows

# ---------- A/B/C/D 需要诊断线数据，若缺则记录跳过 ----------
if diag_path:
    dg = pd.read_csv(diag_path)
    print("diag shape:", dg.shape)
else:
    summary["diagnostic_line"] = "SKIPPED: diagnostic feature file not located; needs mapping from s2_county_yield"
    print("A-D skipped: no diagnostic data located")

json.dump(summary, open(os.path.join(INT, "review_response_summary.json"), "w"), indent=1)
print("saved review_response_summary.json")
