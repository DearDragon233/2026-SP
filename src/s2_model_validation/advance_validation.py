# -*- coding: utf-8 -*-
"""
W4 ADVANCE: 补强管线（Agronomy 审稿加固）
=============================================
缺口 → 解法：
  G1 产量来源敏感性  → 三口径（实测Xiao2024 / 空间预测 / 混合）分别建模对比
  G2 空间CV方案对比  → 纬度块 / 经纬度棋盘块 / 随机CV，量化空间自相关乐观偏差
  G3 QRF不确定性量化 → 分位数区间（10-90%）+ 覆盖率检验 + PICP/MPW 指标
产出：
  Outputs/intermediate/cv_scheme_comparison.csv   CV 方案×模型 对比表
  Outputs/intermediate/qrf_uncertainty.csv        逐网格分位数预测
  Outputs/intermediate/yield_source_sensitivity.csv 敏感性汇总
  Outputs/figures/main/fig04_cv_scheme_comparison.png/.tiff
  Outputs/figures/main/fig07_qrf_uncertainty.png/.tiff
  Outputs/figures/main/fig05_source_sensitivity.png/.tiff
Author: Peng | 2026-09-12
"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from quantile_forest import RandomForestQuantileRegressor

ROOT = r'D:\2026-SP'
ENS   = os.path.join(ROOT, 'Outputs', 'intermediate', 'data_with_yield_ensemble_full.csv')
OUT_INT  = os.path.join(ROOT, 'Outputs', 'intermediate')
OUT_MAIN = os.path.join(ROOT, 'Outputs', 'figures', 'main')
for d in [OUT_INT, OUT_MAIN]: os.makedirs(d, exist_ok=True)

plt.rcParams.update({'font.family':'sans-serif','font.size':9,'figure.dpi':150,
                     'savefig.dpi':600,'savefig.bbox':'tight'})
C = {'blue':'#2F5496','red':'#c5221f','orange':'#e37400','green':'#1b8a4a',
     'grey':'#8c8c8c','purple':'#6a0dad','teal':'#008080'}

RNG = 42

# ============================================================
# LOAD
# ============================================================
print("="*64); print("W4 ADVANCE: Strengthening pipeline"); print("="*64, flush=True)
df = pd.read_csv(ENS)
exclude = ('lon','lat','wheat_yield_tha','wheat_yield_pred_tha','yield_uncertainty_tha',
           'yield_source','yield_blended_tha','yield_uncertainty_blend','yield_source_blend')
feat = [c for c in df.columns if c not in exclude]
lat, lon = df['lat'].values, df['lon'].values
print(f"[0] {len(df)} grids × {len(feat)} features", flush=True)

def make_models():
    return {
        'XGBoost':  XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8, random_state=RNG,
                                 n_jobs=1, verbosity=0),
        'LightGBM': LGBMRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8, random_state=RNG,
                                  n_jobs=1, verbose=-1),
        'RF':       RandomForestRegressor(n_estimators=200, max_depth=7, random_state=RNG, n_jobs=1),
    }

def cv_eval(X, y, groups_fn, tag, rows):
    """按给定分块策略做 5 折 CV，返回逐折指标与拼接预测。rows 直接累积，避免 key 冲突。"""
    res = {}
    for name, mdl in make_models().items():
        folds_r2, folds_rmse = [], []
        y_true_all = np.zeros(len(y)); y_pred_all = np.zeros(len(y))
        for b in np.unique(groups_fn):
            te = groups_fn == b; tr = ~te
            if te.sum() < 8 or tr.sum() < 20: continue
            m = mdl.__class__(**mdl.get_params())
            m.fit(X[tr], y[tr])
            p = m.predict(X[te])
            folds_r2.append(r2_score(y[te], p))
            folds_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
            y_true_all[te] = y[te]; y_pred_all[te] = p
        res[name] = {
            'scheme': tag, 'r2_mean': np.mean(folds_r2), 'r2_std': np.std(folds_r2),
            'rmse_mean': np.mean(folds_rmse), 'rmse_std': np.std(folds_rmse),
            'r2_pooled': r2_score(y_true_all, y_pred_all),
            'y_true': y_true_all, 'y_pred': y_pred_all,
        }
        rows.append({'Scheme': tag, 'Model': name,
                     'R2_mean': round(res[name]['r2_mean'], 4), 'R2_std': round(res[name]['r2_std'], 4),
                     'RMSE_mean': round(res[name]['rmse_mean'], 4), 'RMSE_std': round(res[name]['rmse_std'], 4),
                     'R2_pooled': round(res[name]['r2_pooled'], 4)})
        print(f"    [{tag}] {name:9s}: R²={res[name]['r2_mean']:.4f}±{res[name]['r2_std']:.4f} "
              f"RMSE={res[name]['rmse_mean']:.4f}", flush=True)
    return res

# ============================================================
# G2: SPATIAL CV SCHEMES COMPARISON（纬度块 / 棋盘块 / 随机）
# ============================================================
print("\n[G2] CV scheme comparison (lat-block / checkerboard / random)", flush=True)
X_raw = df[feat].values
scaler = StandardScaler(); X = scaler.fit_transform(X_raw)
y_blend = df['yield_blended_tha'].values

lat_block  = pd.qcut(df['lat'], q=5, labels=False).values
cell = (np.round((lat - lat.min()) / 0.03).astype(int) * 100
        + np.round((lon - lon.min()) / 0.03).astype(int) % 100)
# 棋盘块：把 cell 聚成 5 组（按 cell 哈希均匀分组）
uniq = np.unique(cell)
np.random.seed(RNG); np.random.shuffle(uniq)
cell_map = {c: i % 5 for i, c in enumerate(uniq)}
checker = np.array([cell_map[v] for v in cell])
rng = np.random.RandomState(RNG); random_cv = rng.randint(0, 5, len(y_blend))

scheme_res, rows = {}, []
scheme_res.update(cv_eval(X, y_blend, lat_block, 'lat_block', rows))
scheme_res.update(cv_eval(X, y_blend, checker,  'checker_2d', rows))
scheme_res.update(cv_eval(X, y_blend, random_cv,'random', rows))

cv_comp = pd.DataFrame(rows)
cv_comp.to_csv(os.path.join(OUT_INT, 'cv_scheme_comparison.csv'), index=False, encoding='utf-8-sig')
print("    saved cv_scheme_comparison.csv", flush=True)

# 乐观偏差量化（random - spatial，R² 差）
opt = {}
for mdl in ['XGBoost', 'LightGBM', 'RF']:
    sub = cv_comp[cv_comp.Model==mdl]
    r_rand = sub[sub.Scheme=='random']['R2_mean'].values[0]
    sp_vals = sub[sub.Scheme!='random']['R2_mean'].values
    best_sp = float(sp_vals.max()) if len(sp_vals) else float('nan')
    opt[mdl] = round(r_rand - best_sp, 4)
print(f"    Optimism gap (random - spatial best): {opt}", flush=True)
pd.DataFrame({'Model': list(opt), 'Optimism_R2_gap': list(opt.values())}).to_csv(
    os.path.join(OUT_INT, 'cv_optimism_gap.csv'), index=False, encoding='utf-8-sig')

# ============================================================
# G3: QRF UNCERTAINTY（分位数区间 + 覆盖率）
# ============================================================
print("\n[G3] QRF uncertainty quantification", flush=True)
qrf = RandomForestQuantileRegressor(n_estimators=300, max_depth=9, random_state=RNG, n_jobs=1)
y_true_all, q10_all, q50_all, q90_all = (np.zeros(len(y_blend)) for _ in range(4))
for b in range(5):
    te = lat_block == b; tr = ~te
    qrf.fit(X[tr], y_blend[tr])
    q = qrf.predict(X[te], quantiles=[0.1, 0.5, 0.9])
    q10_all[te], q50_all[te], q90_all[te] = q[:, 0], q[:, 1], q[:, 2]
    y_true_all[te] = y_blend[te]
picp = float(np.mean((y_true_all >= q10_all) & (y_true_all <= q90_all)))
mpw  = float(np.mean(q90_all - q10_all))
r2_q50 = r2_score(y_true_all, q50_all)
rmse_q50 = float(np.sqrt(mean_squared_error(y_true_all, q50_all)))
print(f"    PICP(90%)={picp:.3f}  MPW={mpw:.4f}  Q50 R²={r2_q50:.4f}  RMSE={rmse_q50:.4f}", flush=True)

qrf_out = pd.DataFrame({
    'grid_id': np.arange(len(y_blend)), 'lat': lat, 'lon': lon,
    'y_true_blend': y_true_all, 'q10': q10_all, 'q50': q50_all, 'q90': q90_all,
    'width_90': q90_all - q10_all,
    'covered': ((y_true_all >= q10_all) & (y_true_all <= q90_all)).astype(int),
})
qrf_out.to_csv(os.path.join(OUT_INT, 'qrf_uncertainty.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame({'Metric': ['PICP_90', 'MPW', 'Q50_R2', 'Q50_RMSE'],
              'Value': [round(picp, 4), round(mpw, 4), round(r2_q50, 4), round(rmse_q50, 4)]}).to_csv(
    os.path.join(OUT_INT, 'qrf_metrics.csv'), index=False, encoding='utf-8-sig')
print("    saved qrf_uncertainty.csv / qrf_metrics.csv", flush=True)

# ============================================================
# G1: YIELD SOURCE SENSITIVITY（三口径对比）
# ============================================================
print("\n[G1] Yield source sensitivity (observed / spatial-pred / blend)", flush=True)
y_obs   = df['wheat_yield_tha'].values      # NaN except 43
y_pred  = df['wheat_yield_pred_tha'].values # 234 全预测
mask_obs = ~np.isnan(y_obs)
print(f"    observed n={mask_obs.sum()} | spatial-pred n={len(y_pred)}", flush=True)

sens_rows = []
# 口径A：实测 43 点，随机 5 折
if mask_obs.sum() >= 30:
    Xo, yo = X[mask_obs], y_obs[mask_obs]
    for name, mdl in make_models().items():
        kf = KFold(5, shuffle=True, random_state=RNG)
        p = cross_val_predict(mdl, Xo, yo, cv=kf)
        sens_rows.append({'Target': 'A_observed_43', 'Model': name,
                          'R2': round(r2_score(yo, p), 4),
                          'RMSE': round(float(np.sqrt(mean_squared_error(yo, p))), 4),
                          'MAE': round(float(mean_absolute_error(yo, p)), 4),
                          'n': int(mask_obs.sum())})
        print(f"    [A_obs] {name:9s}: R²={sens_rows[-1]['R2']}", flush=True)
# 口径B：空间预测 234
for name, mdl in make_models().items():
    p = cross_val_predict(mdl, X, y_pred, cv=KFold(5, shuffle=True, random_state=RNG))
    sens_rows.append({'Target': 'B_spatial_pred_234', 'Model': name,
                      'R2': round(r2_score(y_pred, p), 4),
                      'RMSE': round(float(np.sqrt(mean_squared_error(y_pred, p))), 4),
                      'MAE': round(float(mean_absolute_error(y_pred, p)), 4), 'n': 234})
    print(f"    [B_pred] {name:9s}: R²={sens_rows[-1]['R2']}", flush=True)
# 口径C：混合（空间 CV，即 G2 lat_block 结果复用）
for name in ['XGBoost', 'LightGBM', 'RF']:
    v = scheme_res[name]
    sens_rows.append({'Target': 'C_blend_234', 'Model': name,
                      'R2': round(v['r2_mean'], 4), 'RMSE': round(v['rmse_mean'], 4),
                      'MAE': round(float(mean_absolute_error(v['y_true'], v['y_pred'])), 4), 'n': 234})
sens = pd.DataFrame(sens_rows)
sens.to_csv(os.path.join(OUT_INT, 'yield_source_sensitivity.csv'), index=False, encoding='utf-8-sig')
print("    saved yield_source_sensitivity.csv", flush=True)

# ============================================================
# FIG 05: CV SCHEME COMPARISON
# ============================================================
print("\n[FIG] fig05 / fig06 / fig07", flush=True)
fig5, axes = plt.subplots(1, 3, figsize=(18, 5.5))
schemes = ['random', 'lat_block', 'checker_2d']
labels  = ['Random CV\n(optimistic)', 'Latitude\nblock CV', '2D Checkerboard\nCV']
scolors = [C['red'], C['blue'], C['green']]
for ax, mdl in zip(axes, ['XGBoost', 'LightGBM', 'RF']):
    vals = [cv_comp[(cv_comp.Model==mdl)&(cv_comp.Scheme==s)]['R2_mean'].values[0] for s in schemes]
    errs = [cv_comp[(cv_comp.Model==mdl)&(cv_comp.Scheme==s)]['R2_std'].values[0] for s in schemes]
    bars = ax.bar(range(3), vals, yerr=errs, color=scolors, capsize=6, width=0.55, alpha=0.88)
    for i, v in enumerate(vals):
        ax.text(i, v + errs[i] + 0.005, f'{v:.3f}', ha='center', fontweight='bold', fontsize=9)
    gap = vals[0] - max(vals[1], vals[2])
    ax.set_title(f'{mdl}\noptimism gap = {gap:+.3f} R²', fontweight='bold', fontsize=11, loc='left')
    ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel('CV R²' if mdl == 'XGBoost' else '')
    ax.set_ylim(min(0, min(vals) - 0.08), max(vals) + 0.1)
    ax.axhline(0, color=C['grey'], lw=0.6)
    ax.spines[['top', 'right']].set_visible(False)
fig5.suptitle('Spatial CV vs Random CV: quantifying spatial-autocorrelation optimism\n'
              'Blended yield target, 234 grids, 5-fold per scheme', fontweight='bold', fontsize=13, y=1.04)
fig5.savefig(os.path.join(OUT_MAIN, 'fig04_cv_scheme_comparison.png'), dpi=600, facecolor='white')
fig5.savefig(os.path.join(OUT_MAIN, 'fig04_cv_scheme_comparison.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression': 'lzw'})
plt.close(); print("    fig05 done", flush=True)

# ============================================================
# FIG 06: QRF UNCERTAINTY
# ============================================================
fig6, axes6 = plt.subplots(1, 3, figsize=(18, 5.5))
order = np.argsort(y_true_all)
ax = axes6[0]
ax.fill_between(range(len(order)), q10_all[order], q90_all[order],
                color=C['blue'], alpha=0.22, label='Q10–Q90 band')
ax.plot(range(len(order)), y_true_all[order], 'o', ms=2.5, color=C['red'], label='Observed (blend)')
ax.plot(range(len(order)), q50_all[order], '-', lw=1.2, color=C['blue'], label='Q50 prediction')
ax.set_xlabel('Grids sorted by observed yield'); ax.set_ylabel('Yield (t/ha)')
ax.set_title(f'A. QRF prediction intervals\nPICP={picp:.3f}, MPW={mpw:.4f}', fontweight='bold', loc='left')
ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)

ax = axes6[1]
covered = qrf_out['covered'].values
ax.scatter(y_true_all[covered==1], q50_all[covered==1], s=18, alpha=0.6, c=C['green'],
           edgecolors='white', lw=0.3, label=f'covered ({int(covered.sum())})')
ax.scatter(y_true_all[covered==0], q50_all[covered==0], s=26, alpha=0.9, c=C['red'],
           marker='x', label=f'outside ({int((covered==0).sum())})')
mn, mx = y_true_all.min(), y_true_all.max()
ax.fill_between([mn, mx], [mn - (mpw/2)]*2, [mx + (mpw/2)]*2, color=C['grey'], alpha=0.08)
ax.plot([mn, mx], [mn, mx], '--', color=C['grey'], lw=1)
ax.set_xlabel('Observed yield (t/ha)'); ax.set_ylabel('Q50 prediction (t/ha)')
ax.set_title(f'B. Calibration scatter\nQ50 R²={r2_q50:.3f}', fontweight='bold', loc='left')
ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)

ax = axes6[2]
w = qrf_out['width_90'].values
ax.hist(w, bins=24, color=C['purple'], alpha=0.75, edgecolor='white')
ax.axvline(w.mean(), color=C['red'], lw=1.5, ls='--')
ax.text(w.mean(), ax.get_ylim()[1]*0.92, f'mean={w.mean():.3f}', color=C['red'], fontweight='bold')
ax.set_xlabel('Q90–Q10 width (t/ha)'); ax.set_ylabel('Grids')
ax.set_title('C. Interval width distribution\n(narrower = more certain)', fontweight='bold', loc='left')
ax.spines[['top', 'right']].set_visible(False)
fig6.suptitle('Quantile Random Forest uncertainty quantification\n(spatial 5-fold, latitude blocks)', fontweight='bold', fontsize=13, y=1.04)
fig6.savefig(os.path.join(OUT_MAIN, 'fig07_qrf_uncertainty.png'), dpi=600, facecolor='white')
fig6.savefig(os.path.join(OUT_MAIN, 'fig07_qrf_uncertainty.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression': 'lzw'})
plt.close(); print("    fig06 done", flush=True)

# ============================================================
# FIG 07: SOURCE SENSITIVITY
# ============================================================
fig7, axes7 = plt.subplots(1, 2, figsize=(14, 5.5))
ax = axes7[0]
targets = ['A_observed_43', 'B_spatial_pred_234', 'C_blend_234']
tlabels = ['A. Observed\n(43 grids)', 'B. Spatial pred\n(234 grids)', 'C. Blend\n(234 grids)']
mcolors = {'XGBoost': C['blue'], 'LightGBM': C['green'], 'RF': C['orange']}
wdt = 0.25
for i, mdl in enumerate(['XGBoost', 'LightGBM', 'RF']):
    vals = [sens[(sens.Target==t)&(sens.Model==mdl)]['R2'].values[0] for t in targets]
    xs = np.arange(3) + (i - 1) * wdt
    ax.bar(xs, vals, width=wdt, color=mcolors[mdl], label=mdl, alpha=0.88)
    for x, v in zip(xs, vals):
        ax.text(x, v + 0.005, f'{v:.3f}', ha='center', fontsize=7.5, fontweight='bold')
ax.set_xticks(range(3)); ax.set_xticklabels(tlabels, fontsize=9)
ax.set_ylabel('CV R²'); ax.legend(fontsize=8.5, loc='upper right')
ax.set_title('A. Model performance by yield target', fontweight='bold', loc='left')
ax.spines[['top', 'right']].set_visible(False)

ax = axes7[1]
yo, yp = y_obs[mask_obs], y_pred[mask_obs]
lim = [min(yo.min(), yp.min()) - 0.2, max(yo.max(), yp.max()) + 0.2]
ax.scatter(yo, yp, s=40, c=C['blue'], alpha=0.75, edgecolors='white', lw=0.4)
ax.plot(lim, lim, '--', color=C['red'], lw=1.3)
r_sp = np.corrcoef(yo, yp)[0, 1]
ax.set_xlabel('Observed yield (Xiao2024, t/ha)'); ax.set_ylabel('Spatial prediction (t/ha)')
ax.set_title(f'B. Spatial prediction vs observed\nPearson r={r_sp:.3f} (n={mask_obs.sum()})\n'
             f'prediction std={yp.std():.3f} vs observed std={yo.std():.3f}', fontweight='bold', loc='left')
ax.set_xlim(lim); ax.set_ylim(lim)
ax.spines[['top', 'right']].set_visible(False)
fig7.suptitle('Yield-target source sensitivity: is the model learning real variance?\n'
              'Same features; three target constructions compared', fontweight='bold', fontsize=13, y=1.04)
fig7.savefig(os.path.join(OUT_MAIN, 'fig05_source_sensitivity.png'), dpi=600, facecolor='white')
fig7.savefig(os.path.join(OUT_MAIN, 'fig05_source_sensitivity.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression': 'lzw'})
plt.close(); print("    fig07 done", flush=True)

print("\n" + "="*64)
print("W4 ADVANCE COMPLETE")
print("="*64)
print(f"""
Summary:
  G2 CV schemes → cv_scheme_comparison.csv (+optimism gap {opt})
  G3 QRF        → PICP={picp:.3f}, MPW={mpw:.4f}, Q50 R²={r2_q50:.4f}
  G1 Sensitivity→ observed-43 vs pred-234 vs blend; r(obs,pred)={r_sp:.3f}
  Figures: fig05/06/07 (main, 600dpi png+tiff)
""")
