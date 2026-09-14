# -*- coding: utf-8 -*-
"""E 系列实验：同折对比（Goal Brief：R² 提升可量化 + 非过拟合）
基线 E0 = v4 复刻（59 特征，nitrogen 全 NaN 死特征剔除后 58 个）
创新：
  E1 = +年份特异气候（ERA5-Land 2021 生长季 tmean/prec/GDD/EFD 冻融天数 4 列）
  E2 = E1 + 距平特征（2021 年气候 − WorldClim 背景，4 列）
  E3 = E2 + 交互特征（aridity_ws × silt、GDD_ws × clay、prec_cv × elev 等 3 列）
  E4 = E3 + 目标变换 log(y) 训练后逆变换（产量右偏修正）
  E5 = E4 + Optuna 轻调优（40 轮，同折）
全部实验共用同一 5 折划分（seed=42），同折 R² 直接可比。
输出 experiments_ledger.csv + 每个实验的折级明细。
"""
import pandas as pd, numpy as np, json, os, glob, warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")

df = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))
y = df["yield_2021_tha"].values

# ---------- 构建年份特异特征（从 openmeteo 批次 json） ----------
batch_files = sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json")))
print("batches:", len(batch_files))
rows = []
for bf in batch_files:
    j = json.load(open(bf, encoding="utf-8"))
    arr = j if isinstance(j, list) else [j]
    for loc in arr:
        d = loc["daily"]
        t = np.array(d["temperature_2m_mean"], dtype=float)
        tx = np.array(d["temperature_2m_max"], dtype=float)
        tn = np.array(d["temperature_2m_min"], dtype=float)
        p = np.array(d["precipitation_sum"], dtype=float)
        months = np.array([int(s[5:7]) for s in d["time"]])
        # 生长季：10-12 月（2021 属于 2022 收获季，改用 2021 内 1-6 月+前年 10-12 缺）——
        # 采用 2021 自然年内冬小麦关键期 3-6 月（返青-灌浆）+ 全年指标
        m36 = np.isin(months, [3, 4, 5, 6])
        rows.append({
            "lon": round(loc["longitude"], 4), "lat": round(loc["latitude"], 4),
            "y21_tmean": float(np.nanmean(t)),
            "y21_prec": float(np.nansum(p)),
            "y21_t36": float(np.nanmean(t[m36])),          # 返青-灌浆期均温
            "y21_p36": float(np.nansum(p[m36])),           # 返青-灌浆期降水
            "y21_gdd": float(np.nansum(np.maximum(t - 0, 0))),   # 年积温(0°C 基)
            "y21_efd": float(np.nansum(tn < -5)),          # 极端冻害日数(Tmin<-5°C)
            "y21_hot": float(np.nansum(tx > 32)),          # 高温胁迫日数(Tmax>32°C)
        })
clim = pd.DataFrame(rows)
print("climate rows:", len(clim))

# 匹配回 301 网格（lon/lat round 4 位一致）
df["lon_r"] = df["lon"].round(4); df["lat_r"] = df["lat"].round(4)
clim["lon_r"] = clim["lon"].round(4); clim["lat_r"] = clim["lat"].round(4)
mg = df.merge(clim.drop(columns=["lon", "lat"]), on=["lon_r", "lat_r"], how="left")
print("merged climate coverage:", mg["y21_tmean"].notna().sum(), "/301")

# WorldClim 背景距平（bio_1 是 ×10 的年均温）
mg["ano_tmean"] = mg["y21_tmean"] - mg["bio_1"] / 10.0
mg["ano_prec"] = mg["y21_prec"] - mg["bio_12"]
mg["ano_gdd"] = mg["y21_gdd"] - mg["GDD_annual"]
mg["ano_t36"] = mg["y21_t36"] - (mg["bio_10"] / 10.0)  # 最暖季均温背景

# 交互特征
mg["ix_arid_silt"] = mg["aridity_ws"] * mg["silt"]
mg["ix_gdd_clay"] = mg["gdd_ws"] * mg["clay"]
mg["ix_preccv_elev"] = mg["prec_cv"] * mg["elevation_m"]

mg.drop(columns=["lon_r", "lat_r"], inplace=True)
mg.to_csv(os.path.join(INT, "fine250_v5_features.csv"), index=False, encoding="utf-8-sig")
print("v5 feature table saved:", mg.shape)

# ---------- 特征集定义 ----------
base_drop = ["cell_r", "cell_c", "lon", "lat", "lon_r", "lat_r", "yield_2021_tha", "n_px", "nitrogen"]
F0 = [c for c in df.columns if c not in base_drop and df[c].dtype in ("float64", "int64")]
F1 = F0 + ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot"]
F2 = F1 + ["ano_tmean", "ano_prec", "ano_gdd", "ano_t36"]
F3 = F2 + ["ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
print("feature counts: F0=%d F1=%d F2=%d F3=%d" % (len(F0), len(F1), len(F2), len(F3)))

best = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
            colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
            random_state=42, n_jobs=1, verbosity=0)

def run_cv(Xdf, feats, y, log_target=False, params=None, seed=42):
    X = Xdf[feats].values.astype(float)
    X = np.nan_to_num(X, nan=0.0)
    yy = np.log1p(y) if log_target else y
    kf = KFold(5, shuffle=True, random_state=seed)
    fold_rows, yt_all, yp_all = [], np.zeros(len(y)), np.zeros(len(y))
    for f, (tr, te) in enumerate(kf.split(X)):
        sc = StandardScaler().fit(X[tr])
        m = XGBRegressor(**(params or best))
        m.fit(sc.transform(X[tr]), yy[tr])
        pv = m.predict(sc.transform(X[te]))
        if log_target:
            pv = np.expm1(pv); pv = np.clip(pv, 0, None)
            yt = y[te]
        else:
            yt = yy[te]
        yt_all[te] = yt; yp_all[te] = pv
        fold_rows.append({"fold": f, "r2": r2_score(yt, pv),
                          "rmse": np.sqrt(mean_squared_error(yt, pv)),
                          "mae": mean_absolute_error(yt, pv)})
    fr = pd.DataFrame(fold_rows)
    pooled = r2_score(yt_all, yp_all)
    adj = 1 - (1 - pooled) * (len(y) - 1) / (len(y) - len(feats) - 1)
    return {"fold_mean_r2": fr["r2"].mean(), "fold_std": fr["r2"].std(),
            "pooled_r2": pooled, "adj_r2": adj,
            "rmse": fr["rmse"].mean(), "mae": fr["mae"].mean(), "folds": fr}

# ---------- 跑 E0-E4 ----------
ledger = []
for eid, (feats, logt, desc) in {
    "E0_baseline_v4": (F0, False, "v4 复刻：58 特征（剔除死列 nitrogen）"),
    "E1_year_climate": (F1, False, "+2021 年份特异气候 7 列（创新点1）"),
    "E2_anomaly": (F2, False, "+气候距平 4 列（2021-背景）"),
    "E3_interaction": (F3, False, "+交互特征 3 列"),
    "E4_logtarget": (F3, True, "E3 + log 目标变换"),
}.items():
    r = run_cv(mg, feats, y, log_target=logt)
    ledger.append({"exp": eid, "desc": desc, "n_feat": len(feats),
                   "r2_fold_mean": round(r["fold_mean_r2"], 4), "r2_fold_std": round(r["fold_std"], 4),
                   "r2_pooled": round(r["pooled_r2"], 4), "adj_r2": round(r["adj_r2"], 4),
                   "rmse": round(r["rmse"], 4), "mae": round(r["mae"], 4)})
    print(f"{eid}: fold R2={r['fold_mean_r2']:.4f}±{r['fold_std']:.4f} pooled={r['pooled_r2']:.4f} adj={r['adj_r2']:.4f}")

led = pd.DataFrame(ledger)
led.to_csv(os.path.join(INT, "experiments_ledger.csv"), index=False, encoding="utf-8-sig")
print("\nsaved experiments_ledger.csv")

# 最佳折级明细也保存
best_e = led.loc[led["r2_pooled"].idxmax(), "exp"]
print("best so far:", best_e)
