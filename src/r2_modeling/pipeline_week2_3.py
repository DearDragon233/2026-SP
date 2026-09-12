"""
Week 2-3: Complete Modeling Pipeline (Peng's Tasks)
====================================================
Per Yan Jun's directive:
  1. XGBoost + LightGBM + QRF model training with spatial block CV
  2. Boruta feature selection on full 234 grids
  3. SHAP global + feature-level interpretation
  4. Model comparison & performance diagnostics
  5. Paper-ready figures: spatial CV residuals, SHAP summary, feature ranking
  6. Domain-grouped importance with statistical testing

Author: Peng | 2026-07-31
"""

import pandas as pd, numpy as np, os, warnings, time
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
import seaborn as sns
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import KFold, cross_val_score, cross_validate
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import shap

ROOT = r'D:\2026-SP'
ENRICHED = os.path.join(ROOT, 'Outputs', 'intermediate', 'data_with_yield_ensemble.csv')
OUT_MAIN = os.path.join(ROOT, 'Outputs', 'figures', 'main')
OUT_SUPP = os.path.join(ROOT, 'Outputs', 'figures', 'supp')
OUT_INT = os.path.join(ROOT, 'Outputs', 'intermediate')
OUT_MODELS = os.path.join(ROOT, 'Outputs', 'models')
for d in [OUT_MAIN, OUT_SUPP, OUT_INT, OUT_MODELS]: os.makedirs(d, exist_ok=True)

plt.rcParams.update({'font.family':'Arial','font.size':9,'figure.dpi':150,'savefig.dpi':600,'savefig.bbox':'tight'})
C = {'blue':'#2F5496','red':'#c5221f','orange':'#e37400','green':'#1b8a4a','grey':'#8c8c8c',
     'purple':'#6a0dad','teal':'#008080','pink':'#d81b60','gold':'#d4a017'}
DOM_COL = {'Climate':C['blue'],'Soil':C['orange'],'Topography':C['green']}

def classify(v):
    if v.startswith('bio') or v.startswith('tavg_') or v.startswith('prec_') or v.startswith('GDD') or v.startswith('extreme_'): return 'Climate'
    if v in ('clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','ph','nitrogen_cgkg'): return 'Soil'
    if v in ('elevation_m','slope_deg','aspect_deg'): return 'Topography'
    return 'Other'

# ===================================================================
# 1. LOAD DATA
# ===================================================================
print("="*60)
print("WEEK 2-3: MODELING & FEATURE SELECTION PIPELINE")
print("="*60)
df = pd.read_csv(ENRICHED)
print(f"\n[1] Loaded: {len(df)} grids from {ENRICHED}")

feature_cols = [c for c in df.columns if c not in ('lon','lat','wheat_yield_tha','wheat_yield_pred_tha',
                'yield_uncertainty_tha','yield_source','yield_blended_tha','yield_uncertainty_blend','yield_source_blend')]
y = df['yield_blended_tha'].values
X_raw = df[feature_cols].values

# Standardise
scaler = StandardScaler()
X = scaler.fit_transform(X_raw)
print(f"    Features: {len(feature_cols)}, Target range: [{y.min():.2f}, {y.max():.2f}]")

# ===================================================================
# 2. SPATIAL BLOCK CV SETUP
# ===================================================================
print(f"\n[2] Spatial block CV setup...")
# Split grids by latitude to create spatial blocks
lat_blocks = pd.qcut(df['lat'], q=5, labels=False).values
print(f"    5 spatial blocks by latitude")

# ===================================================================
# 3. MODEL TRAINING (XGBoost vs LightGBM vs RF)
# ===================================================================
print(f"\n[3] Training 3 models with spatial block CV...")

models = {
    'XGBoost': XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                            subsample=0.8, colsample_bytree=0.8,
                            reg_alpha=0.1, reg_lambda=1.0,
                            random_state=42, n_jobs=-1, verbosity=0),
    'LightGBM': LGBMRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                              subsample=0.8, colsample_bytree=0.8,
                              reg_alpha=0.1, reg_lambda=1.0,
                              random_state=42, n_jobs=-1, verbose=-1),
    'RF': RandomForestRegressor(n_estimators=300, max_depth=7,
                                random_state=42, n_jobs=-1),
}

results = {}
all_shap = {}
all_preds = {}
all_importances = {}

for name, model in models.items():
    print(f"\n    --- {name} ---")
    fold_r2, fold_rmse, fold_mae = [], [], []
    y_pred_all = np.zeros(len(y))
    y_true_all = np.zeros(len(y))
    fold_imps = []
    shap_fold = []

    for block in range(5):
        test_idx = lat_blocks == block
        train_idx = ~test_idx
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        fold_r2.append(r2_score(y_te, pred))
        fold_rmse.append(np.sqrt(mean_squared_error(y_te, pred)))
        fold_mae.append(mean_absolute_error(y_te, pred))
        y_pred_all[test_idx] = pred
        y_true_all[test_idx] = y_te

        if hasattr(model, 'feature_importances_'):
            fold_imps.append(pd.Series(model.feature_importances_, index=feature_cols))

        # SHAP on test fold (use TreeExplainer)
        if name != 'RF':
            explainer = shap.TreeExplainer(model)
            fold_sv = explainer.shap_values(X_te)
            if isinstance(fold_sv, list):
                fold_sv = fold_sv[0] if len(fold_sv) > 0 else fold_sv
            shap_fold.append(fold_sv)
        else:
            explainer = shap.TreeExplainer(model)
            fold_sv = explainer.shap_values(X_te)
            shap_fold.append(fold_sv)

        print(f"      Block {block+1}: R²={fold_r2[-1]:.3f}, RMSE={fold_rmse[-1]:.4f}, "
              f"MAE={fold_mae[-1]:.4f}, n_test={test_idx.sum()}")

    mean_imp = pd.concat(fold_imps, axis=1).mean(axis=1) if fold_imps else None
    results[name] = {
        'r2_mean': np.mean(fold_r2), 'r2_std': np.std(fold_r2),
        'rmse_mean': np.mean(fold_rmse), 'rmse_std': np.std(fold_rmse),
        'mae_mean': np.mean(fold_mae), 'mae_std': np.std(fold_mae),
        'importance': mean_imp,
    }
    all_preds[name] = (y_true_all, y_pred_all)
    if shap_fold:
        all_shap[name] = np.vstack(shap_fold)
        shap_importance = pd.Series(np.abs(all_shap[name]).mean(axis=0), index=feature_cols)
        results[name]['shap_importance'] = shap_importance

    print(f"      Mean CV: R²={np.mean(fold_r2):.3f}±{np.std(fold_r2):.3f}, "
          f"RMSE={np.mean(fold_rmse):.5f}±{np.std(fold_rmse):.5f}")

# ===================================================================
# 4. BORUTA (XGBoost-based)
# ===================================================================
print(f"\n[4] Boruta feature selection (100 iterations, XGBoost)...")
n_iter = 100
n_shadow = 5
rf_boruta = RandomForestRegressor(n_estimators=200, max_depth=7, random_state=42, n_jobs=-1)

feature_hits = np.zeros(len(feature_cols))
importance_history = np.zeros((n_iter, len(feature_cols)))

for it in range(n_iter):
    X_shadows = np.zeros((X.shape[0], X.shape[1]*n_shadow))
    for j in range(X.shape[1]):
        for s in range(n_shadow):
            X_shadows[:, j*n_shadow+s] = np.random.permutation(X[:, j])
    X_all = np.hstack([X, X_shadows])
    rf_boruta.fit(X_all, y)
    imps = rf_boruta.feature_importances_
    real_imp = imps[:len(feature_cols)]
    shadow_max = imps[len(feature_cols):].max()
    importance_history[it,:] = real_imp
    feature_hits += (real_imp >= shadow_max).astype(int)

    if (it+1) % 25 == 0:
        n_c = (feature_hits >= 99).sum()
        n_t = ((feature_hits < 99) & (feature_hits > 1)).sum()
        n_r = (feature_hits <= 1).sum()
        print(f"    Iter {it+1:3d}: {n_c} confirmed, {n_t} tentative, {n_r} rejected")

hit_rate = feature_hits / n_iter
boruta_class = np.where(hit_rate >= 0.99, 'Confirmed',
               np.where(hit_rate <= 0.01, 'Rejected', 'Tentative'))

# Tentative resolution
if (boruta_class == 'Tentative').any():
    mean_imp = importance_history.mean(axis=0)
    median_shadow = np.median(importance_history[:, boruta_class != 'Confirmed'].max(axis=1))
    for idx in np.where(boruta_class == 'Tentative')[0]:
        boruta_class[idx] = 'Confirmed' if mean_imp[idx] > median_shadow*1.2 else 'Rejected'

n_conf = (boruta_class == 'Confirmed').sum()
n_rej = (boruta_class == 'Rejected').sum()
print(f"    FINAL: {n_conf} confirmed, {n_rej} rejected")

# ===================================================================
# 5. RANKING & THRESHOLD
# ===================================================================
print(f"\n[5] Feature ranking & threshold...")

shap_imp = results['XGBoost']['shap_importance']
ranking = pd.DataFrame({
    'Variable': feature_cols,
    'Domain': [classify(v) for v in feature_cols],
    'SHAP_Importance': shap_imp.values,
    'SHAP_Rank': shap_imp.rank(ascending=False).astype(int),
    'XGB_Importance': results['XGBoost']['importance'].values,
    'Boruta_Class': boruta_class,
    'Hit_Rate': hit_rate,
}).sort_values('SHAP_Importance', ascending=False)

# Domain summary
domain_sum = ranking.groupby('Domain').agg(
    N_Vars=('Variable','count'), N_Confirmed=('Boruta_Class',lambda x:(x=='Confirmed').sum()),
    Mean_SHAP=('SHAP_Importance','mean'), Top10=('SHAP_Rank',lambda x:(x<=10).sum()),
).sort_values('Mean_SHAP', ascending=False)
print(domain_sum.to_string())

# Threshold
cum_imp = np.cumsum(shap_imp.values) / shap_imp.values.sum()
n_80 = np.searchsorted(cum_imp, 0.80) + 1

boruta_conf = ranking[ranking['Boruta_Class']=='Confirmed']['Variable'].tolist()
shap_top = ranking.head(n_80)['Variable'].tolist()
union_vars = list(dict.fromkeys(boruta_conf + shap_top))
print(f"\n    SHAP 80% threshold: top {n_80} vars")
print(f"    Boruta confirmed: {len(boruta_conf)} vars")
print(f"    UNION: {len(union_vars)} vars")
for d in ['Climate','Soil','Topography']:
    cnt = sum(1 for v in union_vars if classify(v)==d)
    print(f"      {d}: {cnt}")

# Save
ranking.to_csv(os.path.join(OUT_INT, 'feature_ranking_full.csv'), index=False, encoding='utf-8-sig')
domain_sum.to_csv(os.path.join(OUT_INT, 'domain_summary.csv'), encoding='utf-8-sig')
pd.DataFrame({'Variable':feature_cols,'Hit_Rate':hit_rate,'Mean_Imp':importance_history.mean(axis=0),'Class':boruta_class}).sort_values('Mean_Imp',ascending=False).to_csv(os.path.join(OUT_INT, 'boruta_results.csv'), index=False, encoding='utf-8-sig')

# ===================================================================
# 6. FIGURES
# ===================================================================
print(f"\n[6] Generating paper figures...")

# --- Fig 2: SHAP Summary Plot ---
fig2, ax2 = plt.subplots(figsize=(10, 14))
top30 = ranking.head(30).sort_values('SHAP_Importance', ascending=True)
colors_top30 = [DOM_COL.get(classify(v), C['grey']) for v in top30['Variable']]
bars = ax2.barh(range(len(top30)), top30['SHAP_Importance'].values, color=colors_top30, height=0.7)
# Mark boruta confirmed
for i, (v, cls) in enumerate(zip(top30['Variable'], top30['Boruta_Class'])):
    if cls == 'Confirmed':
        ax2.text(top30['SHAP_Importance'].values[i]+0.0002, i, '✓', fontsize=8, color=C['green'], fontweight='bold', va='center')
ax2.set_yticks(range(len(top30)))
ax2.set_yticklabels(top30['Variable'], fontsize=8)
ax2.set_xlabel('mean(|SHAP|)')
ax2.set_title('Feature Importance (SHAP) — Top-30\n✓ = Boruta Confirmed', fontweight='bold', fontsize=13, loc='left')
ax2.legend(handles=[Patch(color=c, label=d) for d,c in DOM_COL.items()], fontsize=9, loc='lower right', ncol=3)
fig2.savefig(os.path.join(OUT_MAIN, 'fig02_shap_importance.png'), dpi=600, facecolor='white')
fig2.savefig(os.path.join(OUT_MAIN, 'fig02_shap_importance.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression':'lzw'})
plt.close()
print("    -> fig02_shap_importance.png/tiff")

# --- Fig 3: Model Comparison ---
fig3, axes3 = plt.subplots(1, 3, figsize=(18, 6))

# A: R² bar chart
ax_a = axes3[0]
names = list(models.keys())
r2_vals = [results[n]['r2_mean'] for n in names]
r2_errs = [results[n]['r2_std'] for n in names]
colors_bar = [C['blue'], C['green'], C['orange']]
ax_a.bar(names, r2_vals, yerr=r2_errs, color=colors_bar, capsize=8, width=0.5)
ax_a.set_ylabel('R² (spatial CV)')
ax_a.set_title('A. Model Performance (R²)', fontweight='bold', loc='left')
for i, v in enumerate(r2_vals):
    ax_a.text(i, v+0.01, f'{v:.3f}', ha='center', fontweight='bold', fontsize=10)

# B: Predicted vs Observed (best model)
ax_b = axes3[1]
best_model = max(names, key=lambda n: results[n]['r2_mean'])
yt, yp = all_preds[best_model]
ax_b.scatter(yt, yp, alpha=0.5, s=40, c=C['blue'], edgecolors='white', linewidth=0.3)
mn, mx = yt.min(), yt.max()
ax_b.plot([mn, mx], [mn, mx], '--', color=C['red'], lw=1.5)
ax_b.set_xlabel('Observed'); ax_b.set_ylabel('Predicted')
r2_best = r2_score(yt, yp)
rmse_best = np.sqrt(mean_squared_error(yt, yp))
ax_b.set_title(f'B. {best_model} Predictions\nR²={r2_best:.3f}, RMSE={rmse_best:.5f}', fontweight='bold', loc='left')

# C: Feature importance correlation (XGB vs LGBM)
ax_c = axes3[2]
xgb_imp = results['XGBoost']['importance']
lgbm_imp = results['LightGBM']['importance']
ax_c.scatter(xgb_imp.values, lgbm_imp.values, alpha=0.6, s=30, c=C['purple'], edgecolors='white')
ax_c.set_xlabel('XGBoost Importance'); ax_c.set_ylabel('LightGBM Importance')
r_imp = np.corrcoef(xgb_imp.values, lgbm_imp.values)[0,1]
ax_c.set_title(f'C. Importance Correlation\nr={r_imp:.3f}', fontweight='bold', loc='left')

fig3.savefig(os.path.join(OUT_MAIN, 'fig03_model_comparison.png'), dpi=600, facecolor='white')
fig3.savefig(os.path.join(OUT_MAIN, 'fig03_model_comparison.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression':'lzw'})
plt.close()
print("    -> fig03_model_comparison.png/tiff")

# --- Fig 4: Boruta + Domain Dashboard ---
fig4 = plt.figure(figsize=(20, 12))
gs4 = gridspec.GridSpec(2, 3, figure=fig4, hspace=0.4, wspace=0.35)

ax0 = fig4.add_subplot(gs4[0,0])
boruta_plot = ranking[ranking['Boruta_Class']!='Rejected'].sort_values('SHAP_Importance', ascending=False)
colors_b = [C['green'] if c=='Confirmed' else C['orange'] for c in boruta_plot['Boruta_Class']]
ax0.barh(range(len(boruta_plot)), boruta_plot['SHAP_Importance'].values, color=colors_b, height=0.7)
ax0.set_yticks(range(len(boruta_plot)))
ax0.set_yticklabels(boruta_plot['Variable'], fontsize=7)
ax0.set_xlabel('mean(|SHAP|)')
ax0.set_title(f'A. Boruta + SHAP\n{n_conf} confirmed', fontweight='bold', loc='left', fontsize=11)
ax0.legend(handles=[Patch(color=C['green'],label='Confirmed'),Patch(color=C['orange'],label='Tentative')], fontsize=8)

ax1 = fig4.add_subplot(gs4[0,1])
domain_pie = domain_sum['N_Confirmed'] * domain_sum['Mean_SHAP']
wedges1, texts1, autotexts1 = ax1.pie(domain_pie.values,
    labels=[f'{d}\n({int(r.N_Vars)} vars)' for d,r in domain_sum.iterrows()],
    colors=[DOM_COL.get(d,C['grey']) for d in domain_sum.index],
    autopct='%1.1f%%', textprops={'fontsize':10}, explode=[0.03]*len(domain_sum))
ax1.set_title('B. Domain Contribution', fontweight='bold', loc='left', fontsize=11)

ax2 = fig4.add_subplot(gs4[0,2])
ax2.bar(range(1,len(shap_imp)+1), shap_imp.values, color=[DOM_COL.get(classify(v),C['grey']) for v in shap_imp.index], width=0.8, alpha=0.5)
ax2t = ax2.twinx()
ax2t.plot(range(1,len(shap_imp)+1), cum_imp*100, 'o-', color=C['red'], lw=2, ms=2)
ax2t.axhline(y=80, color=C['green'], ls='--', lw=1)
ax2.set_xlabel('Feature Rank'); ax2.set_ylabel('|SHAP|')
ax2t.set_ylabel('Cumulative %', color=C['red']); ax2t.tick_params(axis='y',labelcolor=C['red'])
ax2.set_title(f'C. Cumulative SHAP\nTop {n_80} = 80%', fontweight='bold', loc='left', fontsize=11)

ax3 = fig4.add_subplot(gs4[1,:2])
top15_shap = all_shap['XGBoost'][:, [feature_cols.index(v) for v in ranking.head(15)['Variable']]]
bp_data = [top15_shap[:, i] for i in range(15)]
bp = ax3.boxplot(bp_data, tick_labels=ranking.head(15)['Variable'].tolist(),
                 patch_artist=True, vert=False, widths=0.6,
                 flierprops={'markersize':2,'alpha':0.3}, medianprops={'color':'red','linewidth':1.5})
for patch in bp['boxes']: patch.set_facecolor(C['blue']); patch.set_alpha(0.3)
ax3.set_xlabel('SHAP Value'); ax3.set_title('D. SHAP Value Distribution (Top-15 features)', fontweight='bold', loc='left', fontsize=11)
ax3.axvline(x=0, color=C['grey'], ls='-', lw=0.8)

ax4 = fig4.add_subplot(gs4[1,2])
ax4.axis('off')
lines_summary = [
    ("MODELING SUMMARY", C['blue'], 13, True), ("", C['grey'], 8, False),
    (f"XGBoost CV R² = {results['XGBoost']['r2_mean']:.3f}±{results['XGBoost']['r2_std']:.3f}", C['green'], 10, True),
    (f"LightGBM CV R² = {results['LightGBM']['r2_mean']:.3f}±{results['LightGBM']['r2_std']:.3f}", C['green'], 10, True),
    (f"RF CV R² = {results['RF']['r2_mean']:.3f}±{results['RF']['r2_std']:.3f}", C['orange'], 10, True),
    ("", C['grey'], 8, False),
    (f"Boruta: {n_conf} confirmed of {len(feature_cols)}", C['purple'], 10, True),
    (f"Recommended: {len(union_vars)} vars (80% SHAP ∪ Boruta)", C['red'], 10, True),
    ("", C['grey'], 8, False),
    ("Domain breakdown:", C['teal'], 10, True),
]
for d in ['Climate','Soil','Topography']:
    lines_summary.append((f"  {d}: {sum(1 for v in union_vars if classify(v)==d)} vars", DOM_COL.get(d,C['grey']), 9, False))
lines_summary.append(("", C['grey'], 8, False))
lines_summary.append(("Spatial CV: 5 blocks by latitude", C['grey'], 9, False))
lines_summary.append(("Yield: Ridge spatial prediction", C['grey'], 9, False))
lines_summary.append(("", C['grey'], 8, False))
lines_summary.append(("NEXT: Week 3-4 → APSIM / NSGA-II", C['green'], 9, True))
for i,(text,color,size,bold) in enumerate(lines_summary):
    ax4.text(0.05, 0.97-i*0.036, text, transform=ax4.transAxes,
             fontsize=size, fontweight='bold' if bold else 'normal', color=color)
ax4.set_title('E. Summary', fontweight='bold', loc='left', fontsize=11)

fig4.savefig(os.path.join(OUT_MAIN, 'fig04_feature_selection_dashboard.png'), dpi=600, facecolor='white')
fig4.savefig(os.path.join(OUT_MAIN, 'fig04_feature_selection_dashboard.tiff'), dpi=600, facecolor='white', pil_kwargs={'compression':'lzw'})
plt.close()
print("    -> fig04_feature_selection_dashboard.png/tiff")

# --- Fig S1-S3: SHAP dependence plots for top features ---
print("    Generating supplementary SHAP dependence plots...")
top3 = ranking.head(3)['Variable'].tolist()
fig_s, axes_s = plt.subplots(1, 3, figsize=(18, 5))
for i, feat in enumerate(top3):
    idx = feature_cols.index(feat)
    shap_values = all_shap['XGBoost'][:, idx]
    feat_values = X[:, idx]
    # Color by another important feature
    color_feat = ranking.head(5).iloc[min(i+1, 4)]['Variable']
    if color_feat == feat: color_feat = ranking.head(5).iloc[0]['Variable']
    color_idx = feature_cols.index(color_feat)
    sc = axes_s[i].scatter(feat_values, shap_values, c=X[:, color_idx], cmap='coolwarm', s=15, alpha=0.6)
    axes_s[i].set_xlabel(feat); axes_s[i].set_ylabel(f'SHAP({feat})')
    axes_s[i].set_title(f'SHAP Dependence: {feat}\ncolored by {color_feat}', fontsize=10)
    cbar = plt.colorbar(sc, ax=axes_s[i]); cbar.set_label(color_feat, fontsize=8)
fig_s.savefig(os.path.join(OUT_SUPP, 'fig_s1_shap_dependence.png'), dpi=300, facecolor='white')
plt.close()
print("    -> fig_s1_shap_dependence.png")

# ===================================================================
# 7. EXPORT MODEL & FINAL REPORT
# ===================================================================
# Retrain best model on all data and save
best_model_name = max(names, key=lambda n: results[n]['r2_mean'])
print(f"\n[7] Best model: {best_model_name}")
final_model = models[best_model_name]
final_model.fit(X, y)

if hasattr(final_model, 'save_model'):
    model_path = os.path.join(OUT_MODELS, f'{best_model_name.lower()}_final.json')
    final_model.save_model(model_path)
    print(f"    Saved: {model_path}")

# Save scaler params
pd.DataFrame({'mean': scaler.mean_, 'scale': scaler.scale_}, index=feature_cols).to_csv(
    os.path.join(OUT_INT, 'scaler_params.csv'), encoding='utf-8-sig')

print(f"\n{'='*60}")
print(f"WEEK 2-3 PIPELINE COMPLETE")
print(f"{'='*60}")
print(f"""
Deliverables:
  fig02_shap_importance.png/tiff    — SHAP Top-30 with Boruta marks
  fig03_model_comparison.png/tiff   — 3-model CV R², pred vs obs, similarity
  fig04_feature_selection_dashboard — Boruta+SHAP+Cumulative+Summary
  fig_s1_shap_dependence.png        — SHAP dependence for top 3 features

Data:
  feature_ranking_full.csv          — 71 features, SHAP+XGB+Boruta rank
  domain_summary.csv                — Domain-level stats
  boruta_results.csv                — Hit rates + classification
  scaler_params.csv                 — For deployment

Key Results:
  Spatial CV (5 blocks by latitude):
    XGBoost  R² = {results['XGBoost']['r2_mean']:.3f} ± {results['XGBoost']['r2_std']:.3f}
    LightGBM R² = {results['LightGBM']['r2_mean']:.3f} ± {results['LightGBM']['r2_std']:.3f}
    RF       R² = {results['RF']['r2_mean']:.3f} ± {results['RF']['r2_std']:.3f}

  Boruta: {n_conf}/{len(feature_cols)} confirmed, {n_rej} rejected
  Recommended: {len(union_vars)} variables (80% SHAP ∪ Boruta Confirmed)

  Top-10 features:
""" + '\n'.join([f'    {i+1:2d}. [{classify(r.Variable):8s}] {r.Variable:25s} |SHAP|={r.SHAP_Importance:.4f}' for i, (_, r) in enumerate(ranking.head(10).iterrows())]))
