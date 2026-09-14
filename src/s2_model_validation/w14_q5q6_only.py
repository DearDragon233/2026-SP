# -*- coding: utf-8 -*-
"""W14 核心实验包（Q1+Q3 合并 / Q2 / Q4 / Q5 / Q6）：
Q1. 块尺寸剂量响应：checker 块边 0.5×/1×/2×/4× 变程（2.3/4.6/9.2/18.4 km → 度数
    lon: km/(111.32*cos40.2)=0.0417°基准；lat: km/110.57）× XGB+RF × 3 种子
    → pooled gap 随块尺寸/变程比曲线（w14_dose_response.csv）
Q3. 嵌套重调参敏感性：诊断数据内 Optuna（20 trial×3 折内 CV）得到嵌套参数组，
    与迁移参数（optuna428）在 random/checker/lat4 下对比 → 结论对超参不敏感则
    gap≈0 非参数伪影（w14_q3_nested_sensitivity.csv）
Q2. 谱系补全：LOBO(KMeans8 坐标) + 24 维环境特征 KMeans4 分块，XGB 3 种子
    → w14_q2_spectrum.csv（随机/checker/lat4/LOBO/环境分块 完整谱系）
Q4. bootstrap CI：A 目标(43) E0 R² 与 C 目标全模型 pooled R²，B=2000 网格重采样
    → w14_q4_bootstrap_ci.json
Q5. 物候期加权特征：从 openmeteo_2021_daily 构造越冬冻害积寒(FDD)与灌浆期高温
    日数(HDF) 2 特征（诊断网格最近邻匹配），加入 24 变量重跑敏感性
    → w14_q5_pheno_features.csv
Q6. 5 种子 + min：random/checker/lat4 主方案扩 5 种子（7/21/42/123/2026）
    → w14_q6_5seeds.csv
"""
import pandas as pd, numpy as np, json, os, warnings, glob
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
df = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble.csv"))
coords = df[["lon", "lat"]].values
drop = {"lon", "lat", "wheat_yield_tha", "yield_blended_tha"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
yC = df["yield_blended_tha"].values
yA = df["wheat_yield_tha"].values
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=2, verbosity=0)
KM_PER_DEG_LON = 111.32 * np.cos(np.radians(40.2))
RANGE_KM = 4.62

def checker_splits(ratio):
    """ratio × 变程作为块边长（km），lon/lat 同步换度数"""
    edge_km = ratio * RANGE_KM
    d = edge_km  # 简化：块边=km，lon 用 cos 校正
    gl = np.floor(coords[:, 0] / (d / KM_PER_DEG_LON)).astype(int)
    ga = np.floor(coords[:, 1] / (d / 110.57)).astype(int)
    ck = (gl + ga) % 2
    return [(np.where(ck != k)[0], np.where(ck == k)[0]) for k in (0, 1)]

def run_splits(splits, feats, y, seed, model="xgb", params=None, frame=None):
    src = frame if frame is not None else df
    X = np.nan_to_num(src[feats].values.astype(float), nan=0.0)
    yp = np.zeros(len(y))
    for tr, te in splits:
        sc = StandardScaler().fit(X[tr])
        if model == "xgb":
            m = XGBRegressor(**{**(params or NEW), "random_state": seed})
        else:
            m = RandomForestRegressor(n_estimators=500, random_state=seed, n_jobs=2)
        m.fit(sc.transform(X[tr]), y[tr]); yp[te] = m.predict(sc.transform(X[te]))
    folds = [r2_score(y[te], yp[te]) for _, te in splits]
    return r2_score(y, yp), float(np.mean(folds))

SEEDS3 = [7, 21, 42]
SEEDS5 = [7, 21, 42, 123, 2026]

# ---------- Q5: 物候期加权特征 ----------
files = sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json")))
pts = []
for fp in files:
    j = json.load(open(fp, encoding="utf-8"))
    records = j if isinstance(j, list) else [j]  # batch_12 为补抓重试格式（单个 dict）
    for r in records:
        d = r["daily"]
        t = pd.to_datetime(d["time"])
        tmin = np.array(d["temperature_2m_min"], dtype=float)
        tmax = np.array(d["temperature_2m_max"], dtype=float)
        mth = t.month
        fdd = float(np.sum(np.clip(0 - tmin, 0, None)[(mth <= 2) | (mth == 12)]))  # 越冬冻害积寒
        hdf = int(np.sum((tmax >= 32) & ((mth == 5) | (mth == 6))))  # 灌浆期高温日数
        pts.append({"lat": r["latitude"], "lon": r["longitude"], "pheno_fdd_winter": fdd, "pheno_hdf_grainfill": hdf})
ph = pd.DataFrame(pts)
from scipy.spatial import cKDTree
tree = cKDTree(ph[["lon", "lat"]].values)
dd, nn = tree.query(coords, k=1)
df2 = df.copy()
df2["pheno_fdd_winter"] = ph["pheno_fdd_winter"].values[nn]
df2["pheno_hdf_grainfill"] = ph["pheno_hdf_grainfill"].values[nn]
print("Q5 snap dist max (deg):", round(float(dd.max()), 4))
FEATS5 = FEATS + ["pheno_fdd_winter", "pheno_hdf_grainfill"]
rows5 = []
for fset, label, frame in [(FEATS, "base24_71", df), (FEATS5, "+pheno2", df2)]:
    ps = []
    for s in SEEDS3:
        p, _ = run_splits(list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1)))), fset, yC, s, "xgb", frame=frame)
        ps.append(p)
    rows5.append({"feature_set": label, "n_feat": len(fset), "pooled_mean": round(np.mean(ps), 4),
                  "pooled_std": round(np.std(ps), 4), "pooled_by_seed": [round(p, 4) for p in ps]})
    print(f"Q5 {label}: {np.mean(ps):.4f}±{np.std(ps):.4f}")
pd.DataFrame(rows5).to_csv(os.path.join(INT, "w14_q5_pheno_features.csv"), index=False, encoding="utf-8-sig")

# ---------- Q6: 5 种子 + min ----------
rows6 = []
for model in ["xgb", "rf"]:
    for scheme in ["random", "checker_1x", "lat4"]:
        ps = []
        for s in SEEDS5:
            if scheme == "random":
                splits = list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1))))
            elif scheme == "lat4":
                latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
                splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
            else:
                splits = checker_splits(1.0)
            p, _ = run_splits(splits, FEATS, yC, s, model)
            ps.append(p)
        rows6.append({"model": model.upper(), "scheme": scheme, "n_seeds": 5, "seeds": SEEDS5,
                      "pooled_mean": round(np.mean(ps), 4), "pooled_std": round(np.std(ps), 4),
                      "pooled_min": round(min(ps), 4), "pooled_by_seed": [round(p, 4) for p in ps]})
        print(f"Q6 {model}/{scheme}: {np.mean(ps):.4f}±{np.std(ps):.4f} min={min(ps):.4f}")
pd.DataFrame(rows6).to_csv(os.path.join(INT, "w14_q6_5seeds.csv"), index=False, encoding="utf-8-sig")
print("W14 experiments done")
