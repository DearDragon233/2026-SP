# -*- coding: utf-8 -*-
"""
W5 STEP2: Zenodo 2021 独立目标 CV 实验
========================================
以 ChinaWheatYield30m 2021（22 网格）为第四产量目标，
用棋盘空间 CV + 随机 CV 两种方案评估三模型。
输出：Outputs/intermediate/zenodo_cv_results.csv
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

ROOT = r'D:\2026-SP'
ENS = os.path.join(ROOT, 'Outputs', 'intermediate', 'zenodo_yield_2021_grid.csv')
OUT_INT = os.path.join(ROOT, 'Outputs', 'intermediate')
RNG = 42

df = pd.read_csv(ENS)
exclude = ('lon','lat','wheat_yield_tha','wheat_yield_pred_tha','yield_uncertainty_tha',
           'yield_source','yield_blended_tha','yield_uncertainty_blend','yield_source_blend',
           'grid_id','zenodo_yield_tha','n_px')
feat = [c for c in df.columns if c not in exclude]

# Zenodo 目标
zmask = df['zenodo_yield_tha'].notna()
Xz_raw = df.loc[zmask, feat].values
yz = df.loc[zmask, 'zenodo_yield_tha'].values
lat_z, lon_z = df.loc[zmask, 'lat'].values, df.loc[zmask, 'lon'].values
sc = StandardScaler(); Xz = sc.fit_transform(Xz_raw)
print(f"Zenodo target: {zmask.sum()} grids, {len(feat)} features")
print(f"  yield: {yz.mean():.2f}±{yz.std():.2f} t/ha")

def make_models():
    return {
        'XGBoost':  XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, random_state=RNG, n_jobs=1, verbosity=0),
        'LightGBM': LGBMRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8, random_state=RNG, n_jobs=1, verbose=-1),
        'RF':       RandomForestRegressor(n_estimators=200, max_depth=7, random_state=RNG, n_jobs=1),
    }

# 棋盘块（22 点较少，用 4 块）
cell = (np.round((lat_z - lat_z.min()) / 0.04).astype(int) * 100 + np.round((lon_z - lon_z.min()) / 0.04).astype(int) % 100)
uniq = np.unique(cell); np.random.seed(RNG); np.random.shuffle(uniq)
cmap = {c: i % 4 for i, c in enumerate(uniq)}
checker = np.array([cmap[v] for v in cell])

rows = []
for scheme, groups in [('checker_4', checker), ('random', None)]:
    if groups is None:
        groups = np.random.RandomState(RNG).randint(0, 4, len(yz))
    for name, mdl in make_models().items():
        f_r2, f_rmse = [], []
        yt_all, yp_all = np.zeros(len(yz)), np.zeros(len(yz))
        for b in np.unique(groups):
            te = groups == b; tr = ~te
            if te.sum() < 3 or tr.sum() < 8: continue
            m = mdl.__class__(**mdl.get_params())
            m.fit(Xz[tr], yz[tr])
            p = m.predict(Xz[te])
            f_r2.append(r2_score(yz[te], p))
            f_rmse.append(np.sqrt(mean_squared_error(yz[te], p)))
            yt_all[te] = yz[te]; yp_all[te] = p
        r = {'Target': 'D_zenodo_2021', 'Scheme': scheme, 'Model': name,
             'R2_mean': round(np.mean(f_r2), 4), 'R2_std': round(np.std(f_r2), 4),
             'RMSE_mean': round(np.mean(f_rmse), 4),
             'R2_pooled': round(r2_score(yt_all, yp_all), 4), 'n': len(yz)}
        rows.append(r)
        print(f"  [{scheme}] {name:9s}: R²={r['R2_mean']:.4f}±{r['R2_std']:.4f} pooled={r['R2_pooled']:.4f}", flush=True)

res = pd.DataFrame(rows)
# 追加到已有敏感性表（如果存在）
sens_path = os.path.join(OUT_INT, 'yield_source_sensitivity.csv')
if os.path.exists(sens_path):
    old = pd.read_csv(sens_path)
    # 旧表结构不同（Target/Model/R2/RMSE/MAE/n），统一格式追加为新文件
    res.to_csv(os.path.join(OUT_INT, 'zenodo_cv_results.csv'), index=False, encoding='utf-8-sig')
else:
    res.to_csv(os.path.join(OUT_INT, 'zenodo_cv_results.csv'), index=False, encoding='utf-8-sig')
print("saved zenodo_cv_results.csv")

# 摘要
print("\n=== ZENODO 2021 INDEPENDENT TARGET ===")
for scheme in ['checker_4', 'random']:
    sub = res[res.Scheme == scheme]
    best = sub.loc[sub.R2_mean.idxmax()]
    print(f"  {scheme}: best = {best.Model} R²={best.R2_mean:.4f}")
print("\nInterpretation: if R² remains low on this independent target,")
print("it confirms with independent data that environmental covariates")
print("explain limited true yield variance at this scale.")
