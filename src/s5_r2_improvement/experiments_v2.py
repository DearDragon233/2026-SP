# -*- coding: utf-8 -*-
"""E 系列 v2：修复合并 bug + 目标尺度问题，扩展实验集
全部实验共用同一 5 折划分（seed=42），同折可比。
  E0 = v4 复刻（58 特征）
  E1 = +2021 年份特异气候 7 列（创新点1，修复合并）
  E2 = E1 + 距平 4 + 交互 3（72 特征）
  E4b = E2 + 折内 z-scored log 目标（修复 L1 压零问题）
  E5 = E2 + 折内增益 top-25 特征选择
  E6 = E5 + 嵌套 Optuna（内 3 折 × 20 试）
  E7 = E2 + Ridge/XGBoost 折内加权混合
  E8 = E2 + 折内残差 IDW 空间修正（诚实标注：随机 CV 下受空间自相关加持）
"""
import pandas as pd, numpy as np, json, os, glob, warnings, time
warnings.filterwarnings("ignore")
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")

df = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))
y = df["yield_2021_tha"].values

# ---------- 气候特征（整数键合并，修复浮点键 bug） ----------
rows = []
for bf in sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json"))):
    j = json.load(open(bf, encoding="utf-8"))
    for loc in (j if isinstance(j, list) else [j]):
        d = loc["daily"]
        t = np.array(d["temperature_2m_mean"], float)
        tx = np.array(d["temperature_2m_max"], float)
        tn = np.array(d["temperature_2m_min"], float)
        p = np.array(d["precipitation_sum"], float)
        months = np.array([int(s[5:7]) for s in d["time"]])
        m36 = np.isin(months, [3, 4, 5, 6])
        rows.append({
            "lon_k": int(round(round(loc["longitude"], 4) * 10000)),
            "lat_k": int(round(round(loc["latitude"], 4) * 10000)),
            "y21_tmean": float(np.nanmean(t)), "y21_prec": float(np.nansum(p)),
            "y21_t36": float(np.nanmean(t[m36])), "y21_p36": float(np.nansum(p[m36])),
            "y21_gdd": float(np.nansum(np.maximum(t, 0))),
            "y21_efd": float(np.nansum(tn < -5)), "y21_hot": float(np.nansum(tx > 32)),
        })
clim = pd.DataFrame(rows)
print("unique ERA5-Land cells:", len(clim))

# 最近邻匹配：Open-Meteo 返回的是 ERA5-Land 网格中心（请求点被吸附到 0.01° 网格），
# 精确键必失配 → 每个 CSV 网格点找最近的气象格心（多个 250m 网格共用 1km 气象格，正常）
C = clim[["lon_k", "lat_k"]].values / 10000.0
P = df[["lon", "lat"]].values
d2 = ((P[:, None, :] - C[None, :, :]) ** 2).sum(-1)
nn_idx = d2.argmin(1)
snap_km = np.sqrt(d2.min(1)) * 111.32
print("snap distance km: median=%.2f p90=%.2f max=%.2f" % (np.median(snap_km), np.percentile(snap_km, 90), snap_km.max()))

clim_matched = clim.iloc[nn_idx].reset_index(drop=True)
CLIM7 = ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot"]
for col in CLIM7:
    df[col] = clim_matched[col].values
cov = df[CLIM7[0]].notna().sum()
print(f"climate coverage: {cov}/301")
assert cov == 301, "merge still failing"

mg = df

mg["ano_tmean"] = mg["y21_tmean"] - mg["bio_1"] / 10.0
mg["ano_prec"] = mg["y21_prec"] - mg["bio_12"]
mg["ano_gdd"] = mg["y21_gdd"] - mg["GDD_annual"]
mg["ano_t36"] = mg["y21_t36"] - mg["bio_10"] / 10.0
mg["ix_arid_silt"] = mg["aridity_ws"] * mg["silt"]
mg["ix_gdd_clay"] = mg["gdd_ws"] * mg["clay"]
mg["ix_preccv_elev"] = mg["prec_cv"] * mg["elevation_m"]
mg.to_csv(os.path.join(INT, "fine250_v5_features.csv"), index=False, encoding="utf-8-sig")

base_drop = ["cell_r", "cell_c", "lon", "lat", "yield_2021_tha", "n_px", "nitrogen"]
F0 = [c for c in df.columns if c not in base_drop and df[c].dtype in ("float64", "int64")]
ANO4 = ["ano_tmean", "ano_prec", "ano_gdd", "ano_t36"]
IX3 = ["ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
F1 = F0 + CLIM7
F2 = F1 + ANO4 + IX3
print("features: F0=%d F1=%d F2=%d" % (len(F0), len(F1), len(F2)))

best_p = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
              colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
              random_state=42, n_jobs=2, verbosity=0)

def metrics(yt, pv):
    return (r2_score(yt, pv), float(np.sqrt(mean_squared_error(yt, pv))), float(mean_absolute_error(yt, pv)))

def eval_pred(yt_all, yp_all, n_feat, name, desc, extra=None):
    pooled, rmse, mae = metrics(yt_all, yp_all)
    adj = 1 - (1 - pooled) * (len(yt_all) - 1) / (len(yt_all) - n_feat - 1)
    fold_r2 = [r2_score(yt_all[te], yp_all[te]) for _, te in KF.split(np.zeros(len(y)))]
    row = {"exp": name, "desc": desc, "n_feat": n_feat,
           "r2_fold_mean": round(np.mean(fold_r2), 4), "r2_fold_std": round(np.std(fold_r2), 4),
           "r2_pooled": round(pooled, 4), "adj_r2": round(adj, 4),
           "rmse": round(rmse, 4), "mae": round(mae, 4)}
    if extra: row.update(extra)
    print(f"{name}: fold={row['r2_fold_mean']}±{row['r2_fold_std']} pooled={row['r2_pooled']} adj={row['adj_r2']}")
    return row

KF = KFold(5, shuffle=True, random_state=42)

def run_XGB(feats, mg_df, y_arr, params=None, logz=False, topk=None, blend_ridge=False,
            resid_idw=False):
    X = np.nan_to_num(mg_df[feats].values.astype(float), nan=0.0)
    yt_all, yp_all, sel_counts = np.zeros(len(y_arr)), np.zeros(len(y_arr)), []
    coords = mg_df[["lon", "lat"]].values
    for tr, te in KF.split(X):
        sc = StandardScaler().fit(X[tr])
        Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        feats_used, params_used = feats, (params or best_p)
        # 折内特征选择（gain importance on train only）
        if topk:
            m0 = XGBRegressor(**best_p); m0.fit(Xtr, y_arr[tr])
            gain = m0.get_booster().get_score(importance_type="gain")
            # 特征名是 f0..fN，映射回列
            idx_gain = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])
            keep = [feats[i] for i, _ in idx_gain[:topk]]
            keep_idx = [feats.index(f) for f in keep]
            Xtr, Xte = Xtr[:, keep_idx], Xte[:, keep_idx]
            feats_used, sel_counts = keep, len(keep)
            params_used = best_p
        yy = y_arr[tr]
        if logz:  # 折内 z-score 的 log 目标（修 L1 压零）
            lt = np.log1p(y_arr[tr])
            mu, sd = lt.mean(), lt.std()
            yy = (lt - mu) / sd
        m = XGBRegressor(**params_used); m.fit(Xtr, yy)
        pv = m.predict(Xte)
        if logz:
            pv = np.expm1(pv * sd + mu); pv = np.clip(pv, 0, None)
        if blend_ridge:
            rg = Ridge(alpha=1.0).fit(Xtr, y_arr[tr])
            pv_r = np.clip(rg.predict(Xte), y_arr.min() - 1, y_arr.max() + 1)
            # 折内在 train 尾部 20% 寻优混合权重
            pv_in = m.predict(Xtr[:int(len(tr)*0.2)])  # 简化：用 0.5/0.5 固定 + 记录
            pv = 0.5 * pv + 0.5 * pv_r
        if resid_idw:
            # 残差 IDW：用 train 折内残差，对 test 点按 4 近邻反距离加权修正
            res_tr = y_arr[tr] - m.predict(Xtr)
            cd = np.sqrt(((coords[te][:, None, :] - coords[tr][None, :, :]) ** 2).sum(-1))
            k = min(8, len(tr))
            nn = np.argsort(cd, axis=1)[:, :k]
            w = 1.0 / np.maximum(cd[np.arange(len(te))[:, None], nn], 1e-3)
            pv = pv + (w * res_tr[nn]).sum(1) / w.sum(1)
        yt_all[te], yp_all[te] = y_arr[te], pv
    return yt_all, yp_all, sel_counts

ledger = []
t0 = time.time()
# E0
yt, yp, _ = run_XGB(F0, mg, y)
ledger.append(eval_pred(yt, yp, len(F0), "E0_baseline_v4", "v4 复刻 58 特征（剔除死列 nitrogen）"))
# E1
yt, yp, _ = run_XGB(F1, mg, y)
ledger.append(eval_pred(yt, yp, len(F1), "E1_year_climate", "+2021 年份特异气候 7 列（创新点1）"))
# E2
yt, yp, _ = run_XGB(F2, mg, y)
ledger.append(eval_pred(yt, yp, len(F2), "E2_full_v5", "+距平 4 + 交互 3（72 特征）"))
# E4b log-z
yt, yp, _ = run_XGB(F2, mg, y, logz=True)
ledger.append(eval_pred(yt, yp, len(F2), "E4b_logz", "E2 + 折内 z-score log 目标"))
# E5 top-25
yt, yp, nsel = run_XGB(F2, mg, y, topk=25)
ledger.append(eval_pred(yt, yp, 25, "E5_topk25", "E2 + 折内增益 top-25 选择", {"sel_note": "fold-internal gain ranking"}))
# E7 ridge blend
yt, yp, _ = run_XGB(F2, mg, y, blend_ridge=True)
ledger.append(eval_pred(yt, yp, len(F2), "E7_ridge_blend", "E2 + Ridge 0.5/0.5 混合"))
# E8 residual IDW
yt, yp, _ = run_XGB(F2, mg, y, resid_idw=True)
ledger.append(eval_pred(yt, yp, len(F2), "E8_resid_idw", "E2 + 折内残差 8 近邻 IDW 修正", {"caution": "随机 CV 受空间自相关加持，需空间 CV 复核"}))

led = pd.DataFrame(ledger)
led.to_csv(os.path.join(INT, "experiments_ledger_v2.csv"), index=False, encoding="utf-8-sig")
print(f"\nelapsed {time.time()-t0:.0f}s, saved experiments_ledger_v2.csv")

# ---------- E6 嵌套 Optuna（最耗时，放最后） ----------
try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    X_all = np.nan_to_num(mg[F2].values.astype(float), nan=0.0)
    # 折内选择 top-25（与 E5 同法，先固定选择再调参）
    sel_by_fold = []
    for tr, te in KF.split(X_all):
        sc = StandardScaler().fit(X_all[tr]); Xtr = sc.transform(X_all[tr])
        m0 = XGBRegressor(**best_p); m0.fit(Xtr, y[tr])
        gain = m0.get_booster().get_score(importance_type="gain")
        idx_gain = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])
        sel_by_fold.append([F2[i] for i, _ in idx_gain[:25]])

    def objective_inner(trial, Xtr_in, ytr_in):
        params = dict(
            n_estimators=trial.suggest_int("n_estimators", 150, 800),
            max_depth=trial.suggest_int("max_depth", 3, 7),
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.3, log=True),
            subsample=trial.suggest_float("subsample", 0.5, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
            min_child_weight=trial.suggest_int("min_child_weight", 1, 15),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10, log=True),
            random_state=42, n_jobs=2, verbosity=0)
        ikf = KFold(3, shuffle=True, random_state=7)
        r2s = []
        Xs = StandardScaler().fit(Xtr_in); Xtr_s = Xs.transform(Xtr_in)
        for itr, ite in ikf.split(Xtr_s):
            mi = XGBRegressor(**params); mi.fit(Xtr_s[itr], ytr_in[itr])
            r2s.append(r2_score(ytr_in[ite], mi.predict(Xtr_s[ite])))
        return float(np.mean(r2s))

    yt_all, yp_all = np.zeros(len(y)), np.zeros(len(y))
    tuned = []
    for f, (tr, te) in enumerate(KF.split(X_all)):
        sc = StandardScaler().fit(X_all[tr])
        Xtr_s = sc.transform(X_all[tr])
        keep_idx = [F2.index(c) for c in sel_by_fold[f]]
        study = optuna.create_study(direction="maximize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(lambda t: objective_inner(t, Xtr_s[:, keep_idx], y[tr]),
                       n_trials=20, show_progress_bar=False)
        bp = study.best_params
        m = XGBRegressor(n_estimators=bp["n_estimators"], max_depth=bp["max_depth"],
                         learning_rate=bp["learning_rate"], subsample=bp["subsample"],
                         colsample_bytree=bp["colsample_bytree"], min_child_weight=bp["min_child_weight"],
                         reg_alpha=bp["reg_alpha"], reg_lambda=bp["reg_lambda"],
                         random_state=42, n_jobs=2, verbosity=0)
        m.fit(Xtr_s[:, keep_idx], y[tr])
        pv = m.predict(sc.transform(X_all[te])[:, keep_idx])
        yt_all[te], yp_all[te] = y[te], pv
        tuned.append({"fold": f, "best_params": bp, "inner_r2": round(study.best_value, 4)})
    row = eval_pred(yt_all, yp_all, 25, "E6_nested_optuna",
                    "E5 + 嵌套 Optuna（内 3 折 × 20 试/折）")
    row["tuned_folds"] = tuned
    ledger.append(row)
    led = pd.DataFrame([{k: v for k, v in r.items() if k != "tuned_folds"} for r in ledger])
    led.to_csv(os.path.join(INT, "experiments_ledger_v2.csv"), index=False, encoding="utf-8-sig")
    json.dump(tuned, open(os.path.join(INT, "e6_tuned_params.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("E6 saved")
except ImportError:
    print("optuna not available, skip E6")

# 保存最佳折级预测用于后续空间 CV 与图表
best_row = led.loc[led["r2_pooled"].idxmax()]
print("\nBEST:", best_row["exp"], "pooled R2 =", best_row["r2_pooled"])
json.dump({"best": str(best_row["exp"]), "ledger": ledger},
          open(os.path.join(INT, "experiments_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1, default=str)
