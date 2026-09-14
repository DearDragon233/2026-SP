# -*- coding: utf-8 -*-
"""E 系列 v3：修正实验标签 + 双模式评估框架
关键修正：F0 在加载后立即快照（v2 的 F0 混入了新特征，标签全部失真）
创新叙事（基于 v2 探索的诚实结论）：
  创新1：折内增益特征精简（小样本下调整 R² 翻倍）
  创新2：Ridge-XGB 折内混合
  创新3：双模式评估框架——mapping mode（含坐标，插值用途）vs transfer mode（无坐标，外推用途），
         随机 CV 与空间分块 CV 双报告（方法学贡献，回应空间 CV 争论）
  负结果1：年份特异气候层（县域内空间变异不足，无增益）——学术上有价值的诚实报告
  负结果2：残差 IDW 在随机 CV 下 0.77 → 空间 CV 下归零（警示虚高）
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

df_raw = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))
y = df_raw["yield_2021_tha"].values
ORIG_NUM = [c for c in df_raw.columns               # ← 原始 58 特征，先快照
            if c not in ("cell_r", "cell_c", "lon", "lat", "yield_2021_tha", "n_px", "nitrogen")
            and df_raw[c].dtype in ("float64", "int64")]
print("original v4 numeric features:", len(ORIG_NUM))

# ---------- 年份气候（从 v5 特征表直接取，已含匹配好的气候列） ----------
v5 = pd.read_csv(os.path.join(INT, "fine250_v5_features.csv"))
CLIM7 = ["y21_tmean", "y21_prec", "y21_t36", "y21_p36", "y21_gdd", "y21_efd", "y21_hot"]
ANO4 = ["ano_tmean", "ano_prec", "ano_gdd", "ano_t36"]
IX3 = ["ix_arid_silt", "ix_gdd_clay", "ix_preccv_elev"]
mg = v5  # 79 列 = 65 原始 + 7 气候 + 4 距平 + 3 交互
assert all(c in mg.columns for c in CLIM7 + ANO4 + IX3)
coords = mg[["lon", "lat"]].values

F0 = ORIG_NUM                    # 58
F1 = F0 + CLIM7                  # 65
F2 = F1 + ANO4 + IX3             # 72
print("F0=%d F1=%d F2=%d" % (len(F0), len(F1), len(F2)))

best_p = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
              colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
              random_state=42, n_jobs=2, verbosity=0)
KF = KFold(5, shuffle=True, random_state=42)
# 空间分块 CV：按纬度 4 分位切 4 块（南北向气候/地形梯度最大）
lat_q = pd.qcut(coords[:, 1], 4, labels=False)
SPATIAL_FOLDS = [(np.where(lat_q != k)[0], np.where(lat_q == k)[0]) for k in range(4)]

def metrics_pooled(yt, yp):
    return (r2_score(yt, yp), float(np.sqrt(mean_squared_error(yt, yp))), float(mean_absolute_error(yt, yp)))

def adj_r2(r2, n, k):
    return 1 - (1 - r2) * (n - 1) / (n - k - 1)

def run(feats, dfm, y_arr, folds, logz=False, topk=None, blend=False, idw=False,
        use_coords=False):
    feats = list(feats) + (["lon", "lat"] if use_coords else [])
    X = np.nan_to_num(dfm[feats].values.astype(float), nan=0.0)
    yt_all, yp_all = np.zeros(len(y_arr)), np.zeros(len(y_arr))
    fold_r2s = []
    for tr, te in folds:
        sc = StandardScaler().fit(X[tr])
        Xtr, Xte = sc.transform(X[tr]), sc.transform(X[te])
        feats_used, k_eff = feats, len(feats)
        if topk:
            m0 = XGBRegressor(**best_p); m0.fit(Xtr, y_arr[tr])
            gain = m0.get_booster().get_score(importance_type="gain")
            idx_gain = sorted(((int(k[1:]), v) for k, v in gain.items()), key=lambda x: -x[1])
            keep = [feats[i] for i, _ in idx_gain[:topk]]
            keep_idx = [feats.index(f) for f in keep]
            Xtr, Xte, feats_used, k_eff = Xtr[:, keep_idx], Xte[:, keep_idx], keep, len(keep)
        yy = y_arr[tr]
        if logz:
            lt = np.log1p(y_arr[tr]); mu, sd = lt.mean(), lt.std()
            yy = (lt - mu) / sd
        m = XGBRegressor(**best_p); m.fit(Xtr, yy)
        pv = m.predict(Xte)
        if logz:
            pv = np.clip(np.expm1(pv * sd + mu), 0, None)
        if blend:
            rg = Ridge(alpha=1.0).fit(Xtr, y_arr[tr])
            pv_r = rg.predict(Xte)
            pv = 0.5 * pv + 0.5 * pv_r
        if idw:
            res_tr = y_arr[tr] - m.predict(Xtr)
            cd = np.sqrt(((coords[te][:, None, :] - coords[tr][None, :, :]) ** 2).sum(-1))
            k = min(8, len(tr))
            nn = np.argsort(cd, axis=1)[:, :k]
            w = 1.0 / np.maximum(cd[np.arange(len(te))[:, None], nn], 1e-3)
            pv = pv + (w * res_tr[nn]).sum(1) / w.sum(1)
        yt_all[te], yp_all[te] = y_arr[te], pv
        fold_r2s.append(r2_score(y_arr[te], pv))
    return yt_all, yp_all, fold_r2s, k_eff

ledger = []
def record(name, desc, yt, yp, k_eff, fold_r2s, extra=None):
    pooled, rmse, mae = metrics_pooled(yt, yp)
    row = {"exp": name, "desc": desc, "n_feat": k_eff,
           "r2_fold_mean": round(np.mean(fold_r2s), 4), "r2_fold_std": round(np.std(fold_r2s), 4),
           "r2_pooled": round(pooled, 4), "adj_r2": round(adj_r2(pooled, len(y), k_eff), 4),
           "rmse": round(rmse, 4), "mae": round(mae, 4)}
    if extra: row.update(extra)
    print(f"{name}: fold={row['r2_fold_mean']}±{row['r2_fold_std']} pooled={row['r2_pooled']} adj={row['adj_r2']}")
    ledger.append(row)
    return row

preds_store = {}
t0 = time.time()
A = "transfer"  # —— A 组：transfer mode（无坐标）
yt, yp, fr, k = run(F0, mg, y, KF.split(np.zeros(len(y))))
record("E0_base58", "v4 基线复刻（58 特征，无坐标）", yt, yp, k, fr); preds_store["E0"] = (yt, yp)
yt, yp, fr, k = run(F1, mg, y, KF.split(np.zeros(len(y))))
record("E1_clim7", "+2021 年份特异气候 7 列", yt, yp, k, fr)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))))
record("E2_v5full", "+距平 4+交互 3（72 特征）", yt, yp, k, fr); preds_store["E2"] = (yt, yp)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))), topk=25)
record("E5_topk25", "E2+折内增益 top-25 精简（创新1）", yt, yp, k, fr); preds_store["E5"] = (yt, yp)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))), topk=25, blend=True)
record("E7_topk25_ridge", "E5+Ridge 0.5 混合（创新2）", yt, yp, k, fr); preds_store["E7"] = (yt, yp)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))), idw=True)
record("E8_resid_idw", "E2+折内残差 IDW（负结果展示）", yt, yp, k, fr,
       {"caution": "random-CV inflation expected"}); preds_store["E8"] = (yt, yp)

B = "mapping"  # —— B 组：mapping mode（含坐标，插值用途）
yt, yp, fr, k = run(F0, mg, y, KF.split(np.zeros(len(y))), use_coords=True)
record("M0_base58_xy", "基线+lon/lat（mapping mode）", yt, yp, k, fr); preds_store["M0"] = (yt, yp)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))), topk=25, use_coords=True)
record("M5_topk25_xy", "E5+lon/lat（mapping mode）", yt, yp, k, fr); preds_store["M5"] = (yt, yp)
yt, yp, fr, k = run(F2, mg, y, KF.split(np.zeros(len(y))), topk=25, blend=True, use_coords=True)
record("M7_topk25_ridge_xy", "E7+lon/lat（mapping mode）", yt, yp, k, fr); preds_store["M7"] = (yt, yp)

# —— C 组：空间分块 CV（4 纬度块，诚实外推检验）——
print("\n--- spatial blocked CV (4 lat blocks) ---")
sp_rows = []
for name, kw in [("S0_base58", dict(feats=F0)),
                 ("S5_topk25", dict(feats=F2, topk=25)),
                 ("S8_resid_idw", dict(feats=F2, idw=True)),
                 ("SM5_topk25_xy", dict(feats=F2, topk=25, use_coords=True))]:
    yt, yp, fr, k = run(kw["feats"], mg, y, SPATIAL_FOLDS, topk=kw.get("topk"),
                        blend=kw.get("blend", False), idw=kw.get("idw", False),
                        use_coords=kw.get("use_coords", False))
    pooled, rmse, mae = metrics_pooled(yt, yp)
    r = {"exp": name, "cv": "spatial4", "r2_pooled": round(pooled, 4),
         "rmse": round(rmse, 4), "mae": round(mae, 4),
         "fold_r2s": [round(x, 3) for x in fr]}
    print(f"{name}: spatial pooled={r['r2_pooled']} folds={r['fold_r2s']}")
    sp_rows.append(r)
    preds_store[name] = (yt, yp)

led = pd.DataFrame(ledger)
led.to_csv(os.path.join(INT, "experiments_ledger_v3.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(sp_rows).to_csv(os.path.join(INT, "spatial_cv_ledger.csv"), index=False, encoding="utf-8-sig")
# 保存全部预测，供图表与复用
pd.DataFrame({k: v[0] for k, v in preds_store.items()}).assign(
    **{k + "_p": v[1] for k, v in preds_store.items()}).to_csv(
    os.path.join(INT, "all_predictions_v3.csv"), index=False, encoding="utf-8-sig")
print(f"\nelapsed {time.time()-t0:.0f}s — ledgers+predictions saved")
best = led.loc[led["r2_pooled"].idxmax()]
best_adj = led.loc[led["adj_r2"].idxmax()]
print("BEST pooled:", best["exp"], best["r2_pooled"], "| BEST adj:", best_adj["exp"], best_adj["adj_r2"])
