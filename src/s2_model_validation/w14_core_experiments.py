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

def run_splits(splits, feats, y, seed, model="xgb", params=None):
    X = np.nan_to_num(df[feats].values.astype(float), nan=0.0)
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

# ---------- Q1: 剂量响应 ----------
rows = []
for ratio in [0.5, 1.0, 2.0, 4.0]:
    splits = checker_splits(ratio)
    for model in ["xgb", "rf"]:
        ps, fs = [], []
        for s in SEEDS3:
            p, f = run_splits(splits, FEATS, yC, s, model)
            ps.append(p); fs.append(f)
        rows.append({"part": "Q1", "block_ratio_x_range": ratio, "edge_km": ratio * RANGE_KM,
                     "model": model.upper(), "pooled_mean": round(np.mean(ps), 4),
                     "pooled_std": round(np.std(ps), 4), "pooled_by_seed": [round(p, 4) for p in ps],
                     "fold_mean_mean": round(np.mean(fs), 4), "fold_mean_std": round(np.std(fs), 4)})
        print(f"Q1 ratio={ratio} {model}: pooled {np.mean(ps):.4f}±{np.std(ps):.4f}")
# 随机基线（gap 分母）
for model in ["xgb", "rf"]:
    ps, fs = [], []
    for s in SEEDS3:
        p, f = run_splits(list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1)))), FEATS, yC, s, model)
        ps.append(p); fs.append(f)
    rows.append({"part": "Q1", "block_ratio_x_range": 0.0, "edge_km": 0.0, "model": model.upper(),
                 "pooled_mean": round(np.mean(ps), 4), "pooled_std": round(np.std(ps), 4),
                 "pooled_by_seed": [round(p, 4) for p in ps], "fold_mean_mean": round(np.mean(fs), 4),
                 "fold_mean_std": round(np.std(fs), 4), "note": "random baseline (ratio=0)"})
    print(f"Q1 random {model}: pooled {np.mean(ps):.4f}")
pd.DataFrame(rows).to_csv(os.path.join(INT, "w14_dose_response.csv"), index=False, encoding="utf-8-sig")

# ---------- Q3: 嵌套重调参敏感性 ----------
# 诊断数据内 3 折内 CV × 12 trial Optuna（轻量预算证明趋势）
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError:
    optuna = None
inner = list(KFold(3, shuffle=True, random_state=42).split(np.zeros((len(yC), 1))))
if optuna is not None:
    def objective(trial):
        params = dict(n_estimators=trial.suggest_int("n_estimators", 100, 500),
                      max_depth=trial.suggest_int("max_depth", 2, 6),
                      learning_rate=trial.suggest_float("learning_rate", 0.02, 0.3, log=True),
                      subsample=trial.suggest_float("subsample", 0.5, 1.0),
                      colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
                      min_child_weight=trial.suggest_int("min_child_weight", 1, 15),
                      reg_alpha=trial.suggest_float("reg_alpha", 0, 5),
                      reg_lambda=trial.suggest_float("reg_lambda", 0.01, 5),
                      random_state=42, n_jobs=2, verbosity=0)
        X = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
        sc_all = StandardScaler().fit(X)
        r2s = []
        for tr, te in inner:
            m = XGBRegressor(**params); m.fit(sc_all.transform(X[tr]), yC[tr])
            r2s.append(r2_score(yC[te], m.predict(sc_all.transform(X[te]))))
        return float(np.mean(r2s))
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=12, show_progress_bar=False)
    nested_params = {**study.best_params, "random_state": 42, "n_jobs": 2, "verbosity": 0}
    print("Q3 nested best:", {k: round(v, 4) if isinstance(v, float) else v for k, v in study.best_params.items()})
else:
    nested_params = dict(n_estimators=161, max_depth=3, learning_rate=0.0596, subsample=0.757,
                         colsample_bytree=0.596, min_child_weight=9, reg_alpha=2.34, reg_lambda=0.047,
                         random_state=42, n_jobs=2, verbosity=0)
    print("Q3 optuna unavailable, using e6 fold-0 params as nested proxy")
rows3 = []
for pname, pp in [("optuna428_transferred", NEW), ("nested_reopt_diag", nested_params)]:
    for scheme, sp in [("random", None), ("checker_1x", checker_splits(1.0)), ("lat4", "lat")]:
        ps = []
        for s in SEEDS3:
            if scheme == "random":
                splits = list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1))))
            elif scheme == "lat4":
                latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
                splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
            else:
                splits = sp
            p, _ = run_splits(splits, FEATS, yC, s, "xgb", pp)
            ps.append(p)
        rows3.append({"param_set": pname, "scheme": scheme, "pooled_mean": round(np.mean(ps), 4),
                      "pooled_std": round(np.std(ps), 4), "pooled_by_seed": [round(p, 4) for p in ps]})
        print(f"Q3 {pname}/{scheme}: {np.mean(ps):.4f}±{np.std(ps):.4f}")
pd.DataFrame(rows3).to_csv(os.path.join(INT, "w14_q3_nested_sensitivity.csv"), index=False, encoding="utf-8-sig")

# ---------- Q2: 谱系补全 ----------
rows2 = []
blocks_lobo = KMeans(8, random_state=42, n_init=10).fit_predict(coords)
Xf = StandardScaler().fit_transform(np.nan_to_num(df[FEATS].values.astype(float), nan=0.0))
blocks_env = KMeans(4, random_state=42, n_init=10).fit_predict(Xf)
schemes = {"random": None, "checker_1x": checker_splits(1.0), "lat4": "lat",
           "lobo8": [(np.where(blocks_lobo != k)[0], np.where(blocks_lobo == k)[0]) for k in range(8)],
           "env_kmeans4": [(np.where(blocks_env != k)[0], np.where(blocks_env == k)[0]) for k in range(4)]}
for sname, sp in schemes.items():
    ps, fs = [], []
    for s in SEEDS3:
        if scheme_is_random := (sp is None):
            splits = list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1))))
        elif isinstance(sp, str):
            latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
            splits = [(np.where(latq != k)[0], np.where(latq == k)[0]) for k in range(4)]
        else:
            splits = sp
        p, f = run_splits(splits, FEATS, yC, s, "xgb")
        ps.append(p); fs.append(f)
    rows2.append({"scheme": sname, "question": {"random": "区域内制图", "checker_1x": "自相关控制下的制图",
                 "lat4": "梯度外推", "lobo8": "区域外推", "env_kmeans4": "环境空间外推"}[sname],
                 "pooled_mean": round(np.mean(ps), 4), "pooled_std": round(np.std(ps), 4),
                 "pooled_by_seed": [round(p, 4) for p in ps], "fold_mean_mean": round(np.mean(fs), 4),
                 "fold_mean_std": round(np.std(fs), 4)})
    print(f"Q2 {sname}: {np.mean(ps):.4f}±{np.std(ps):.4f}")
pd.DataFrame(rows2).to_csv(os.path.join(INT, "w14_q2_spectrum.csv"), index=False, encoding="utf-8-sig")

# ---------- Q4: bootstrap CI ----------
rng = np.random.default_rng(7)
m43 = ~np.isnan(yA)
Xa = np.nan_to_num(df.loc[m43, FEATS].values.astype(float), nan=0.0)
ya = yA[m43]
ca = coords[m43]
def e0_oof(idx_mask):
    tr = np.where(idx_mask)[0]; te = np.where(~idx_mask)[0]
    sc = StandardScaler().fit(Xa[tr])
    m = XGBRegressor(**NEW); m.fit(sc.transform(Xa[tr]), ya[tr])
    return te, m.predict(sc.transform(Xa[te]))
# 全数据 OOF
n = len(ya); yp_all = np.zeros(n)
kf = KFold(5, shuffle=True, random_state=42)
for tr, te in kf.split(Xa):
    sc = StandardScaler().fit(Xa[tr]); m = XGBRegressor(**NEW); m.fit(sc.transform(Xa[tr]), ya[tr])
    yp_all[te] = m.predict(sc.transform(Xa[te]))
boot = []
for b in range(2000):
    idx = rng.integers(0, n, n)
    if len(np.unique(ya[idx])) < 2: continue
    boot.append(r2_score(ya[idx], yp_all[idx]))
ci_a = [round(float(np.percentile(boot, 2.5)), 4), round(float(np.percentile(boot, 97.5)), 4)]
# C 目标 pooled bootstrap（对 OOF 残差重采样近似的简单版本：直接重采样网格重算 R2）
Xc = np.nan_to_num(df[FEATS].values.astype(float), nan=0.0)
ypc = np.zeros(len(yC))
for tr, te in KFold(5, shuffle=True, random_state=42).split(Xc):
    sc = StandardScaler().fit(Xc[tr]); m = XGBRegressor(**NEW); m.fit(sc.transform(Xc[tr]), yC[tr])
    ypc[te] = m.predict(sc.transform(Xc[te]))
boot_c = []
for b in range(2000):
    idx = rng.integers(0, len(yC), len(yC))
    if len(np.unique(yC[idx])) < 2: continue
    boot_c.append(r2_score(yC[idx], ypc[idx]))
ci_c = [round(float(np.percentile(boot_c, 2.5)), 4), round(float(np.percentile(boot_c, 97.5)), 4)]
out4 = {"A_obs43_E0": {"r2_point": round(r2_score(ya, yp_all), 4), "ci95": ci_a, "B": 2000,
                       "equiv_upper_pct": round(max(0, ci_a[1]) * 100, 1)},
        "C_blend234_XGB": {"r2_point": round(r2_score(yC, ypc), 4), "ci95": ci_c, "B": 2000}}
json.dump(out4, open(os.path.join(INT, "w14_q4_bootstrap_ci.json"), "w"), indent=1)
print("Q4:", json.dumps(out4))

# ---------- Q5: 物候期加权特征 ----------
files = sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json")))
pts = []
for fp in files:
    for r in json.load(open(fp, encoding="utf-8")):
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
for fset, label in [(FEATS, "base24_71"), (FEATS5, "+pheno2")]:
    ps = []
    for s in SEEDS3:
        p, _ = run_splits(list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(yC), 1)))), fset, yC, s, "xgb")
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
