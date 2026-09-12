# -*- coding: utf-8 -*-
"""
W6 FIG: 补制 fig01 研究区地图 + fig08 独立源验证图
fig01: 平谷区 234 网格 + 产量来源分布（A 区域区位；B 网格与产量来源；C 数据源柱状）
fig08: Zenodo 2021 独立目标 CV 结果（A 网格分布；B R² 对比；C 解读要点）
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import numpy as np, pandas as pd, os

plt.rcParams.update({'font.family':'sans-serif','font.size':9,'figure.dpi':150,
                     'savefig.dpi':600,'savefig.bbox':'tight'})
C = {'blue':'#2F5496','red':'#c5221f','orange':'#e37400','green':'#1b8a4a',
     'grey':'#8c8c8c','purple':'#6a0dad','teal':'#008080'}

ROOT = r'D:\2026-SP'
OUT_MAIN = os.path.join(ROOT, 'Outputs', 'figures', 'main')
ENS = os.path.join(ROOT, 'Outputs', 'intermediate', 'data_with_yield_ensemble_full.csv')
ZEN = os.path.join(ROOT, 'Outputs', 'intermediate', 'zenodo_yield_2021_grid.csv')
df = pd.read_csv(ENS)
zen = pd.read_csv(ZEN) if os.path.exists(ZEN) else None

# ============ FIG 01: STUDY AREA MAP ============
fig = plt.figure(figsize=(14, 10))
gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1, 1.3], hspace=0.35, wspace=0.3)

# A: 区位图（华北放大示意，示意性——不依赖 basemap/cartopy）
axA = fig.add_subplot(gs[0, :2])
axA.set_xlim(112, 122); axA.set_ylim(35, 43)
# 画一个简化的中国东部轮廓（仅几个关键城市标注，示意）
axA.plot([116.4], [39.9], 's', color=C['red'], ms=8, zorder=5)
axA.annotate('Beijing', (116.4, 39.9), textcoords="offset points", xytext=(8, 6), fontsize=10, fontweight='bold')
axA.plot([117.1], [40.13], '^', color=C['blue'], ms=10, zorder=5)
axA.annotate('Pinggu\n(study area)', (117.1, 40.13), textcoords="offset points", xytext=(10, 8), fontsize=10, fontweight='bold', color=C['blue'])
# 简化省份边界示意
for city, lon, lat in [('Shijiazhuang', 114.5, 38.0), ('Tianjin', 117.2, 39.1), ('Zhangjiakou', 114.9, 40.8)]:
    axA.plot([lon], [lat], 'o', color=C['grey'], ms=4)
    axA.annotate(city, (lon, lat), textcoords="offset points", xytext=(5, -10), fontsize=8, color=C['grey'])
# 华北平原范围框
rect = mpatches.FancyBboxPatch((116.7, 39.7), 0.7, 0.6, boxstyle="round,pad=0.05",
                                fill=False, edgecolor=C['blue'], lw=1.5, linestyle='--')
axA.add_patch(rect)
axA.set_title('A. Location of Pinggu District, Beijing', fontweight='bold', loc='left', fontsize=12)
axA.set_xlabel('Longitude (°E)'); axA.set_ylabel('Latitude (°N)')
axA.spines[['top', 'right']].set_visible(False)

# B: 数据源柱状
axB = fig.add_subplot(gs[0, 2])
sources = ['Xiao2024\n(observed)', 'Ridge interp\n(spatial pred)', 'Bayesian\nblend', 'ChinaWheat\nYield30m 2021']
counts = [43, 234, 234, 22]
colors_s = [C['red'], C['blue'], C['purple'], C['green']]
bars = axB.barh(range(4), counts, color=colors_s, alpha=0.8, height=0.6)
for i, v in enumerate(counts):
    axB.text(v + 3, i, str(v), va='center', fontweight='bold', fontsize=10)
axB.set_yticks(range(4)); axB.set_yticklabels(sources, fontsize=9)
axB.set_xlabel('Number of grids with yield data')
axB.set_title('B. Yield data sources', fontweight='bold', loc='left', fontsize=12)
axB.invert_yaxis(); axB.spines[['top', 'right']].set_visible(False)

# C: 234 网格散点（按产量来源着色）
axC = fig.add_subplot(gs[1, :])
sc1 = axC.scatter(df['lon'], df['lat'], s=18, c=C['grey'], alpha=0.35, label='No yield (0 grids)' if False else 'All grids (n=234)')
mask_obs = df['wheat_yield_tha'].notna()
axC.scatter(df.loc[mask_obs, 'lon'], df.loc[mask_obs, 'lat'], s=40, c=C['red'],
            edgecolors='white', lw=0.5, label=f'Observed Xiao2024 (n={mask_obs.sum()})', zorder=5)
# Zenodo 网格
if zen is not None and 'zenodo_yield_tha' in zen.columns:
    mz = zen['zenodo_yield_tha'].notna()
    axC.scatter(zen.loc[mz, 'lon'], zen.loc[mz, 'lat'], s=50, facecolors='none',
                edgecolors=C['green'], lw=1.5, marker='s', label=f'ChinaWheatYield30m (n={mz.sum()})', zorder=6)
# 标注乡镇名
for name, lon, lat in [('Yukou', 117.06, 40.15), ('Dahuashan', 117.09, 40.21), ('Xifangezhuang', 117.06, 40.15),
                        ('Xiayuan', 117.18, 40.14), ('Shandongzhuang', 117.15, 40.16)]:
    axC.annotate(name, (lon, lat), textcoords="offset points", xytext=(6, 4), fontsize=7.5, color=C['blue'], fontweight='bold')
axC.set_xlabel('Longitude (°E)'); axC.set_ylabel('Latitude (°N)')
axC.set_title('C. Study area: 234 grids (3.5 km) with yield data availability', fontweight='bold', loc='left', fontsize=12)
axC.legend(fontsize=9, loc='upper right')
axC.spines[['top', 'right']].set_visible(False)

fig.suptitle('Study area: Pinggu District, Beijing — 234 grid environmental fingerprint matrix with four yield data sources',
             fontweight='bold', fontsize=13, y=1.02)
fig.savefig(os.path.join(OUT_MAIN, 'fig01_study_area.png'), dpi=600, facecolor='white')
fig.savefig(os.path.join(OUT_MAIN, 'fig01_study_area.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression': 'lzw'})
plt.close(); print("fig01 done", flush=True)

# ============ FIG 08: INDEPENDENT SOURCE VALIDATION ============
cv_path = os.path.join(ROOT, 'Outputs', 'intermediate', 'zenodo_cv_results.csv')
if os.path.exists(cv_path):
    cvz = pd.read_csv(cv_path)
    fig8, axes8 = plt.subplots(1, 3, figsize=(17, 5.5))

    # A: R² 对比（checker vs random）
    ax = axes8[0]
    models = ['XGBoost', 'LightGBM', 'RF']
    for i, mdl in enumerate(models):
        vals = []
        for scheme in ['checker_4', 'random']:
            sub = cvz[(cvz.Model == mdl) & (cvz.Scheme == scheme)]
            vals.append(sub['R2_mean'].values[0] if len(sub) else np.nan)
        xs = np.arange(2) + (i - 1) * 0.22
        mcolors = {'XGBoost': C['blue'], 'LightGBM': C['green'], 'RF': C['orange']}
        ax.bar(xs, vals, width=0.2, color=mcolors[mdl], label=mdl, alpha=0.85)
        for x, v in zip(xs, vals):
            if not np.isnan(v):
                ax.text(x, v + (0.02 if v > 0 else -0.08), f'{v:.3f}', ha='center', fontsize=8, fontweight='bold')
    ax.axhline(0, color=C['grey'], lw=0.8)
    ax.set_xticks([0, 1]); ax.set_xticklabels(['Checkerboard\nCV', 'Random CV'], fontsize=9.5)
    ax.set_ylabel('R²')
    ax.set_title('A. Model performance on independent\nChinaWheatYield30m target (22 grids)', fontweight='bold', loc='left')
    ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)

    # B: 网格空间分布（Zenodo 有值的 22 个网格）
    ax = axes8[1]
    if zen is not None and 'zenodo_yield_tha' in zen.columns:
        mz = zen['zenodo_yield_tha'].notna()
        sc = ax.scatter(zen.loc[mz, 'lon'], zen.loc[mz, 'lat'], c=zen.loc[mz, 'zenodo_yield_tha'],
                        cmap='YlGn', s=90, edgecolors='white', lw=0.8, vmin=4.5, vmax=7.5)
        plt.colorbar(sc, ax=ax, label='Yield (t/ha)')
    ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
    ax.set_title('B. Spatial distribution of Zenodo 2021\nwinter wheat yield (22 valid grids)', fontweight='bold', loc='left')
    ax.spines[['top', 'right']].set_visible(False)

    # C: 四目标 R² 汇总
    ax = axes8[2]
    targets = ['A. Observed', 'B. Spat.pred', 'C. Blend', 'D. Zenodo']
    r2s = [-0.02, 0.98, 0.39, cvz[(cvz.Scheme == 'checker_4')]['R2_mean'].mean() if len(cvz) else 0]
    # 用实际值覆盖
    if os.path.exists(os.path.join(ROOT, 'Outputs', 'intermediate', 'yield_source_sensitivity.csv')):
        sens = pd.read_csv(os.path.join(ROOT, 'Outputs', 'intermediate', 'yield_source_sensitivity.csv'))
        for i, t in enumerate(['A_observed_43', 'B_spatial_pred_234', 'C_blend_234']):
            best = sens[sens.Target == t]['R2'].max()
            r2s[i] = best
    if len(cvz):
        r2s[3] = cvz[(cvz.Scheme == 'checker_4')]['R2_mean'].values[0] if len(cvz[cvz.Scheme == 'checker_4']) else r2s[3]
    colors_t = [C['red'], C['blue'], C['purple'], C['green']]
    ax.barh(range(4), r2s, color=colors_t, alpha=0.85, height=0.55)
    for i, v in enumerate(r2s):
        ax.text(v + (0.01 if v > 0 else -0.04), i, f'{v:.3f}', va='center', fontweight='bold', fontsize=9)
    ax.axvline(0, color=C['grey'], lw=0.8)
    ax.set_yticks(range(4)); ax.set_yticklabels(targets, fontsize=9.5)
    ax.set_xlabel('Best model R² (spatial CV)')
    ax.set_title('C. Four yield targets: apparent R²\n(low target quality → low or inflated R²)', fontweight='bold', loc='left')
    ax.invert_yaxis(); ax.spines[['top', 'right']].set_visible(False)

    fig8.suptitle('Independent data source validation: ChinaWheatYield30m 2021 confirms minimal environmental predictive capacity',
                  fontweight='bold', fontsize=12, y=1.03)
    fig8.savefig(os.path.join(OUT_MAIN, 'fig08_independent_validation.png'), dpi=600, facecolor='white')
    fig8.savefig(os.path.join(OUT_MAIN, 'fig08_independent_validation.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression': 'lzw'})
    plt.close(); print("fig08 done", flush=True)
else:
    print("zenodo_cv_results.csv not found, fig08 skipped")
