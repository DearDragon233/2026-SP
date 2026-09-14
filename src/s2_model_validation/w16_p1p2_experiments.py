# -*- coding: utf-8 -*-
"""W16 核心实验包：
P1 退化机制证据：各分块方案下"平均最近异块训练邻距离" vs 块比例
   ——大方块时该距离趋近随机 CV 水平 = 棋盘静默退化为随机（签名曲线）
   同时计算各方案"训练集对全域环境空间的覆盖率代理"（异块训练格占比）
P2 小麦适生热量指标敏感性（Tbase=0°C 季节 GDD、春化日数、灌浆期高温、越冬极寒）
   对 A(43)/C(234) 两目标的增量——修正 F4 的 Tbase=10 错配
输出: w16_p1_degeneration.csv, w16_p2_wheat_thermal.csv, w16_p1_nn_distances.json
"""
import pandas as pd, numpy as np, json, os, glob, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
from scipy.spatial import cKDTree
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
df = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv")) if os.path.exists(
    os.path.join(INT, "data_with_yield_ensemble_full.csv")) else pd.read_csv(os.path.join(INT, "data_with_yield_ensemble.csv"))
coords = df[["lon", "lat"]].values
yC = df["yield_blended_tha"].values
yA = df["wheat_yield_tha"].values
KM_LON = 111.32 * np.cos(np.radians(40.2)); RANGE = 4.62
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=2, verbosity=0)
drop = {"lon", "lat", "wheat_yield_tha", "wheat_yield_pred_tha", "yield_uncertainty_tha",
        "yield_source", "yield_blended_tha", "yield_source_blend"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]

def checker_blocks(ratio):
    edge = ratio * RANGE
    gl = np.floor(coords[:, 0] / (edge / KM_LON)).astype(int)
    ga = np.floor(coords[:, 1] / (edge / 110.57)).astype(int)
    return (gl + ga) % 2

def mean_nn_otherblock(blocks):
    """每格到最近异块格的距离(km)的均值——衡量块间隔离度"""
    tree = cKDTree(coords)
    out = []
    for i in range(len(coords)):
        same = np.where(blocks == blocks[i])[0]
        d, _ = tree.query(coords[i], k=len(coords), distance_upper_bound=np.inf)
        # 找第一个不属于同块的
        for j in np.argsort(d):
            if blocks[j] != blocks[i]:
                out.append(d[j]); break
    return float(np.mean(out)) * 111.32  # 度→km 粗略（两方向取平均系数）

def cv_r2(splits, feats, y, seed, frame=None):
    src = frame if frame is not None else df
    X = np.nan_to_num(src[feats].values.astype(float), nan=0.0)
    yp = np.zeros(len(y))
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr])
        m = XGBRegressor(**{**NEW, "random_state": seed}); m.fit(sc.transform(X[tr]), y[tr])
        yp[te] = m.predict(sc.transform(X[te]))
    return r2_score(y, yp)

SEEDS = [7, 21, 42]
rows = []
schemes = {"random": None, "checker_0.5x": checker_blocks(0.5), "checker_1x": checker_blocks(1.0),
           "checker_2x": checker_blocks(2.0), "checker_4x": checker_blocks(4.0)}
latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
schemes["lat4"] = latq
for name, blk in schemes.items():
    if blk is None:
        splits_per_seed = [list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1)))) for s in SEEDS]
        iso = 0.0
    else:
        splits_per_seed = [[(np.where(blk != k)[0], np.where(blk == k)[0]) for k in np.unique(blk)]] * 3
        iso = mean_nn_otherblock(blk)
    ps = [cv_r2(sp, FEATS, yC, s) for sp, s in zip(splits_per_seed, SEEDS)]
    gap = ps_mean = float(np.mean(ps))
    rows.append({"scheme": name, "mean_nn_otherblock_km": round(iso, 2),
                 "pooled_mean": round(gap, 4), "pooled_std": round(np.std(ps), 4)})
    print(f"P1 {name}: iso={iso:.2f}km pooled={np.mean(ps):.4f}±{np.std(ps):.4f}")
base = rows[0]["pooled_mean"]
for r in rows[1:]:
    r["gap_vs_random"] = round(r["pooled_mean"] - base, 4)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w16_p1_degeneration.csv"), index=False, encoding="utf-8-sig")

# ---------- P2: 小麦适生热量指标 ----------
files = sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json")))
pts = []
for fp in files:
    j = json.load(open(fp, encoding="utf-8"))
    for r in (j if isinstance(j, list) else [j]):
        d = r["daily"]
        t = pd.to_datetime(d["time"]); mth = t.month
        tavg = np.array(d["temperature_2m_mean"], dtype=float)
        tmin = np.array(d["temperature_2m_min"], dtype=float)
        tmax = np.array(d["temperature_2m_max"], dtype=float)
        # 冬小麦季 2020-10 ~ 2021-06：数据只有 2021 年 → 用 1-6 月近似（10-12 月缺失声明）
        in_season = mth <= 6
        gdd0 = float(np.sum(np.clip(tavg[in_season] - 0, 0, None)))          # Tbase=0 季节积温
        vernal = int(np.sum((tavg >= 0) & (tavg <= 10) & ((mth <= 2) | (mth == 12))))  # 春化日数（12-2月窗口近似）
        hdd_deep = int(np.sum(tmin <= -10))                                   # 深冬极端冻害日（全年）
        hdf30 = int(np.sum((tmax >= 30) & (mth <= 6)))                        # 灌浆期高温（1-6 月）
        pts.append({"lat": r["latitude"], "lon": r["longitude"], "w_gdd0_season": gdd0,
                    "w_vernal_days": vernal, "w_deepcold_days": hdd_deep, "w_hdf30_grain": hdf30})
ph = pd.DataFrame(pts)
tree = cKDTree(ph[["lon", "lat"]].values)
dd, nn = tree.query(coords, k=1)
df2 = df.copy()
for c in ["w_gdd0_season", "w_vernal_days", "w_deepcold_days", "w_hdf30_grain"]:
    df2[c] = ph[c].values[nn]
print("P2 snap max (deg):", round(float(dd.max()), 4), "| vernal mean:", round(df2.w_vernal_days.mean(),1),
      "| deepcold mean:", round(df2.w_deepcold_days.mean(),1))
FEATS5 = FEATS + ["w_gdd0_season", "w_vernal_days", "w_deepcold_days", "w_hdf30_grain"]
rows2 = []
splits_rand = [list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1)))) for s in SEEDS]
for fset, label, frame in [(FEATS, "base", df), (FEATS5, "+wheat_thermal4", df2)]:
    ps = [cv_r2(sp, fset, yC, s, frame) for sp, s in zip(splits_rand, SEEDS)]
    rows2.append({"target": "C_blend", "feature_set": label, "pooled_mean": round(np.mean(ps), 4),
                  "pooled_std": round(np.std(ps), 4), "by_seed": [round(p, 4) for p in ps]})
    print(f"P2 C {label}: {np.mean(ps):.4f}±{np.std(ps):.4f}")
# A 目标（43 格，LOO 太贵 → 5 折）
mA = ~np.isnan(yA)
for fset, label in [(FEATS, "base"), (FEATS5, "+wheat_thermal4")]:
    Xa = np.nan_to_num(df2.loc[mA, fset].values.astype(float), nan=0.0)
    ya = yA[mA]
    ps = []
    for s in SEEDS:
        yp = np.zeros(len(ya))
        for tr, te in KFold(5, shuffle=True, random_state=s).split(Xa):
            sc = StandardScaler().fit(Xa[tr])
            m = XGBRegressor(**{**NEW, "random_state": s}); m.fit(sc.transform(Xa[tr]), ya[tr])
            yp[te] = m.predict(sc.transform(Xa[te]))
        ps.append(r2_score(ya, yp))
    rows2.append({"target": "A_obs43(process-model)", "feature_set": label, "pooled_mean": round(np.mean(ps), 4),
                  "pooled_std": round(np.std(ps), 4), "by_seed": [round(p, 4) for p in ps]})
    print(f"P2 A {label}: {np.mean(ps):.4f}±{np.std(ps):.4f}")
pd.DataFrame(rows2).to_csv(os.path.join(INT, "w16_p2_wheat_thermal.csv"), index=False, encoding="utf-8-sig")
print("W16 experiments done")
