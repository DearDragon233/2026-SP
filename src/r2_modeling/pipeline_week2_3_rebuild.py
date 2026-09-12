"""
Week 2-3 REBUILD: Modeling pipeline with county-level ensemble yield
========================================================================
Quick rebuild using Bayesian ensemble yield.
Spatial CV + 3 models + Boruta (50 iter) + SHAP + figures.
"""
import pandas as pd, numpy as np, os, warnings, sys
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

ROOT = r'D:\2026-SP'; os.makedirs(ROOT, exist_ok=True)
ENRICHED = os.path.join(ROOT, 'Outputs', 'intermediate', 'data_with_yield_ensemble.csv')
OUT_MAIN = os.path.join(ROOT, 'Outputs', 'figures', 'main')
OUT_SUPP = os.path.join(ROOT, 'Outputs', 'figures', 'supp')
OUT_INT  = os.path.join(ROOT, 'Outputs', 'intermediate')
OUT_MODELS=os.path.join(ROOT, 'Outputs', 'models')
for d in [OUT_MAIN, OUT_SUPP, OUT_INT, OUT_MODELS]: os.makedirs(d, exist_ok=True)

plt.rcParams.update({'font.family':'sans-serif','font.size':9,'figure.dpi':150,'savefig.dpi':600,
                     'savefig.bbox':'tight'})
C = {'blue':'#2F5496','red':'#c5221f','orange':'#e37400','green':'#1b8a4a','grey':'#8c8c8c',
     'purple':'#6a0dad','teal':'#008080'}
DOM_COL = {'Climate':C['blue'],'Soil':C['orange'],'Topography':C['green']}

def classify(v):
    if v.startswith(('bio','tavg_','prec_','GDD','extreme_')): return 'Climate'
    if v in ('clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','ph','nitrogen_cgkg'): return 'Soil'
    if v in ('elevation_m','slope_deg','aspect_deg'): return 'Topography'
    return 'Other'

# ────────────────────────────────────────────
# 1. LOAD
# ────────────────────────────────────────────
print("="*60, flush=True)
print("WEEK 2-3 REBUILD: County-Yield Ensemble Modeling", flush=True)
print("="*60, flush=True)

df = pd.read_csv(ENRICHED)
exclude = ('lon','lat','wheat_yield_tha','wheat_yield_pred_tha','yield_uncertainty_tha',
           'yield_source','yield_blended_tha','yield_uncertainty_blend','yield_source_blend')
feature_cols = [c for c in df.columns if c not in exclude]
y = df['yield_blended_tha'].values
X_raw = df[feature_cols].values

scaler = StandardScaler(); X = scaler.fit_transform(X_raw)
print(f"[1] Loaded: {len(df)} grids, {len(feature_cols)} features", flush=True)
print(f"    Yield: {y.mean():.2f} ± {y.std():.2f} t/ha, range=[{y.min():.2f}, {y.max():.2f}]", flush=True)

# ────────────────────────────────────────────
# 2. SPATIAL CV
# ────────────────────────────────────────────
lat_blocks = pd.qcut(df['lat'], q=5, labels=False).values
print(f"[2] 5 spatial blocks by latitude", flush=True)

# ────────────────────────────────────────────
# 3. MODELS
# ────────────────────────────────────────────
print(f"[3] Training 3 models...", flush=True)
models = {
    'XGBoost':  XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                             subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbosity=0),
    'LightGBM': LGBMRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                              subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbose=-1),
    'RF':       RandomForestRegressor(n_estimators=200, max_depth=7, random_state=42, n_jobs=1),
}
results, all_preds = {}, {}

for name, mdl in models.items():
    fold_r2, fold_rmse, fold_mae = [], [], []
    y_pred_all, y_true_all = np.zeros(len(y)), np.zeros(len(y))
    for b in range(5):
        te = lat_blocks==b; tr = ~te
        mdl.fit(X[tr], y[tr])
        p = mdl.predict(X[te])
        fold_r2.append(r2_score(y[te], p))
        fold_rmse.append(np.sqrt(mean_squared_error(y[te], p)))
        fold_mae.append(np.abs(y[te]-p).mean())
        y_pred_all[te]=p; y_true_all[te]=y[te]
    results[name] = {'r2_mean':np.mean(fold_r2),'r2_std':np.std(fold_r2),
                     'rmse_mean':np.mean(fold_rmse),'rmse_std':np.std(fold_rmse),
                     'mae_mean':np.mean(fold_mae),'importance': pd.Series(mdl.feature_importances_, index=feature_cols)}
    all_preds[name] = (y_true_all, y_pred_all)
    print(f"    {name:10s}: CV R²={np.mean(fold_r2):.4f}±{np.std(fold_r2):.4f}  RMSE={np.mean(fold_rmse):.4f}±{np.std(fold_rmse):.4f}", flush=True)

# ────────────────────────────────────────────
# 4. SHAP (re-train on all data)
# ────────────────────────────────────────────
print(f"[4] SHAP (XGBoost retrain on all data)...", flush=True)
xgb_full = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=1, verbosity=0)
xgb_full.fit(X, y)
import shap
explainer = shap.TreeExplainer(xgb_full)
shap_vals = explainer.shap_values(X)
if isinstance(shap_vals, list): shap_vals = shap_vals[0] if len(shap_vals)>0 else shap_vals
shap_imp = pd.Series(np.abs(shap_vals).mean(axis=0), index=feature_cols)
print(f"    SHAP computed, top-5: {list(shap_imp.nlargest(5).index)}", flush=True)

# ────────────────────────────────────────────
# 5. BORUTA (50 iterations)
# ────────────────────────────────────────────
print(f"[5] Boruta (50 iterations, RF)...", flush=True)
n_iter, n_shadow = 50, 5
rf_bor = RandomForestRegressor(n_estimators=150, max_depth=7, random_state=42, n_jobs=1)
hits = np.zeros(len(feature_cols))
imps_hist = np.zeros((n_iter, len(feature_cols)))
for it in range(n_iter):
    X_sh = np.zeros((X.shape[0], X.shape[1]*n_shadow))
    for j in range(X.shape[1]):
        for s in range(n_shadow):
            X_sh[:, j*n_shadow+s] = np.random.permutation(X[:, j])
    X_all = np.hstack([X, X_sh])
    rf_bor.fit(X_all, y)
    imps = rf_bor.feature_importances_
    real_imp = imps[:len(feature_cols)]; shadow_max = imps[len(feature_cols):].max()
    imps_hist[it,:] = real_imp
    hits += (real_imp >= shadow_max).astype(int)
    if (it+1)%25==0:
        print(f"    iter {it+1:2d}: {(hits>=49).sum()} confirmed, {((hits<49)&(hits>1)).sum()} tentative, {(hits<=1).sum()} rejected", flush=True)

hit_rate = hits/n_iter
bor_cls = np.where(hit_rate>=0.98, 'Confirmed', np.where(hit_rate<=0.02, 'Rejected', 'Tentative'))
# Resolve tentative
if (bor_cls=='Tentative').any():
    median_shadow = np.median(imps_hist[:, bor_cls!='Confirmed'].max(axis=1))
    for idx in np.where(bor_cls=='Tentative')[0]:
        bor_cls[idx] = 'Confirmed' if imps_hist[:,idx].mean() > median_shadow*1.2 else 'Rejected'

n_conf = (bor_cls=='Confirmed').sum(); n_rej = (bor_cls=='Rejected').sum()
print(f"    FINAL: {n_conf} confirmed, {n_rej} rejected", flush=True)

# ────────────────────────────────────────────
# 6. RANKING
# ────────────────────────────────────────────
print(f"[6] Ranking & threshold...", flush=True)
ranking = pd.DataFrame({
    'Variable':feature_cols,'Domain':[classify(v) for v in feature_cols],
    'SHAP_Importance':shap_imp.values,'SHAP_Rank':shap_imp.rank(ascending=False).astype(int),
    'XGB_Importance':xgb_full.feature_importances_,'Boruta_Class':bor_cls,'Hit_Rate':hit_rate,
}).sort_values('SHAP_Importance', ascending=False)

domain_sum = ranking.groupby('Domain').agg(
    N_Vars=('Variable','count'),N_Confirmed=('Boruta_Class',lambda x:(x=='Confirmed').sum()),
    Mean_SHAP=('SHAP_Importance','mean'),Top10=('SHAP_Rank',lambda x:(x<=10).sum()),
).sort_values('Mean_SHAP', ascending=False)

cum_imp = np.cumsum(shap_imp.values)/shap_imp.values.sum()
n_80 = np.searchsorted(cum_imp, 0.80)+1
bor_conf = ranking[ranking['Boruta_Class']=='Confirmed']['Variable'].tolist()
shap_top = ranking.head(n_80)['Variable'].tolist()
union_vars = list(dict.fromkeys(bor_conf+shap_top))

best_model = max(models.keys(), key=lambda n: results[n]['r2_mean'])
print(f"\n    Best model: {best_model} (R²={results[best_model]['r2_mean']:.4f})")
print(f"    Boruta: {n_conf} confirmed / {n_rej} rejected")
print(f"    SHAP 80%: top {n_80} vars")
print(f"    UNION: {len(union_vars)} vars")
for d in ['Climate','Soil','Topography']:
    print(f"      {d}: {sum(1 for v in union_vars if classify(v)==d)}")
print(f"\n    Top-10:")
for i,(_,r) in enumerate(ranking.head(10).iterrows()):
    print(f"    {i+1:2d}. [{classify(r.Variable):8s}] {r.Variable:25s} |SHAP|={r.SHAP_Importance:.5f}  {'✓' if r.Boruta_Class=='Confirmed' else ''}")

ranking.to_csv(os.path.join(OUT_INT,'feature_ranking_full.csv'),index=False,encoding='utf-8-sig')
domain_sum.to_csv(os.path.join(OUT_INT,'domain_summary.csv'),encoding='utf-8-sig')
pd.DataFrame({'Variable':feature_cols,'Hit_Rate':hit_rate,'Mean_Imp':imps_hist.mean(axis=0),'Class':bor_cls}).sort_values('Mean_Imp',ascending=False).to_csv(os.path.join(OUT_INT,'boruta_results.csv'),index=False,encoding='utf-8-sig')
pd.DataFrame({'mean':scaler.mean_,'scale':scaler.scale_},index=feature_cols).to_csv(os.path.join(OUT_INT,'scaler_params.csv'),encoding='utf-8-sig')

# ────────────────────────────────────────────
# 7. FIG:02 SHAP IMPORTANCE
# ────────────────────────────────────────────
print(f"[7] Generating figures...", flush=True)

fig2, ax2 = plt.subplots(figsize=(10,14))
top30 = ranking.head(30).sort_values('SHAP_Importance', ascending=True)
colors_top = [DOM_COL.get(classify(v),C['grey']) for v in top30['Variable']]
ax2.barh(range(len(top30)), top30['SHAP_Importance'].values, color=colors_top, height=0.7)
for i,(v,cls) in enumerate(zip(top30['Variable'],top30['Boruta_Class'])):
    if cls=='Confirmed':
        ax2.text(top30['SHAP_Importance'].values[i]+0.0005, i, '✓', fontsize=8, color=C['green'], fontweight='bold', va='center')
ax2.set_yticks(range(len(top30))); ax2.set_yticklabels(top30['Variable'],fontsize=8)
ax2.set_xlabel('mean(|SHAP|)')
ax2.set_title('Feature Importance (SHAP) — Top-30\nCounty-Yield Ensemble | ✓ = Boruta Confirmed', fontweight='bold', fontsize=13, loc='left')
ax2.legend(handles=[Patch(color=c,label=d) for d,c in DOM_COL.items()],fontsize=9,loc='lower right',ncol=3)
fig2.savefig(os.path.join(OUT_MAIN,'fig02_shap_importance.png'),dpi=600,facecolor='white')
fig2.savefig(os.path.join(OUT_MAIN,'fig02_shap_importance.tiff'),dpi=600,facecolor='white',pil_kwargs={'compression':'lzw'})
plt.close(); print("    fig02_shap_importance", flush=True)

# ────────────────────────────────────────────
# 8. FIG:03 MODEL COMPARISON
# ────────────────────────────────────────────
fig3, axes3 = plt.subplots(1,3,figsize=(18,6))
ax_a = axes3[0]
names = list(models.keys())
r2_v = [results[n]['r2_mean'] for n in names]
r2_e = [results[n]['r2_std'] for n in names]
colors_b = [C['blue'],C['green'],C['orange']]
ax_a.bar(names,r2_v,yerr=r2_e,color=colors_b,capsize=8,width=0.5)
ax_a.set_ylabel('R² (spatial CV)'); ax_a.set_title('A. Model Performance', fontweight='bold', loc='left')
for i,v in enumerate(r2_v): ax_a.text(i,v+0.01,f'{v:.3f}',ha='center',fontweight='bold',fontsize=10)

ax_b = axes3[1]
yt,yp = all_preds[best_model]
ax_b.scatter(yt,yp,alpha=0.5,s=40,c=C['blue'],edgecolors='white',linewidth=0.3)
mn,mx = yt.min(),yt.max()
ax_b.plot([mn,mx],[mn,mx],'--',color=C['red'],lw=1.5)
ax_b.set_xlabel('Observed'); ax_b.set_ylabel('Predicted')
ax_b.set_title(f'B. {best_model} Predictions\nR²={r2_score(yt,yp):.3f}, RMSE={np.sqrt(mean_squared_error(yt,yp)):.4f}', fontweight='bold', loc='left')

ax_c = axes3[2]
xgb_i=results['XGBoost']['importance']; lgbm_i=results['LightGBM']['importance']
ax_c.scatter(xgb_i.values,lgbm_i.values,alpha=0.6,s=30,c=C['purple'],edgecolors='white')
ax_c.set_xlabel('XGBoost Importance'); ax_c.set_ylabel('LightGBM Importance')
r_imp=np.corrcoef(xgb_i.values,lgbm_i.values)[0,1]
ax_c.set_title(f'C. Importance Correlation\nr={r_imp:.3f}',fontweight='bold',loc='left')
fig3.savefig(os.path.join(OUT_MAIN,'fig03_model_comparison.png'),dpi=600,facecolor='white')
fig3.savefig(os.path.join(OUT_MAIN,'fig03_model_comparison.tiff'),dpi=600,facecolor='white',pil_kwargs={'compression':'lzw'})
plt.close(); print("    fig03_model_comparison", flush=True)

# ────────────────────────────────────────────
# 9. FIG:04 DASHBOARD
# ────────────────────────────────────────────
fig4 = plt.figure(figsize=(20,12))
gs4 = gridspec.GridSpec(2,3,figure=fig4,hspace=0.4,wspace=0.35)

ax0=fig4.add_subplot(gs4[0,0])
bor_plot=ranking[ranking['Boruta_Class']!='Rejected'].sort_values('SHAP_Importance',ascending=False)
col_b=[C['green'] if c=='Confirmed' else C['orange'] for c in bor_plot['Boruta_Class']]
ax0.barh(range(len(bor_plot)),bor_plot['SHAP_Importance'].values,color=col_b,height=0.7)
ax0.set_yticks(range(len(bor_plot))); ax0.set_yticklabels(bor_plot['Variable'],fontsize=7)
ax0.set_xlabel('mean(|SHAP|)')
ax0.set_title(f'A. Boruta + SHAP\n{n_conf} confirmed',fontweight='bold',loc='left',fontsize=11)
ax0.legend(handles=[Patch(color=C['green'],label='Confirmed'),Patch(color=C['orange'],label='Tentative')],fontsize=8)

ax1=fig4.add_subplot(gs4[0,1])
dp=domain_sum['N_Confirmed']*domain_sum['Mean_SHAP']
ax1.pie(dp.values,labels=[f'{d}\n({int(r.N_Vars)} vars)' for d,r in domain_sum.iterrows()],
        colors=[DOM_COL.get(d,C['grey']) for d in domain_sum.index],
        autopct='%1.1f%%',textprops={'fontsize':10},explode=[0.03]*len(domain_sum))
ax1.set_title('B. Domain Contribution',fontweight='bold',loc='left',fontsize=11)

ax2_=fig4.add_subplot(gs4[0,2])
ax2_.bar(range(1,len(shap_imp)+1),shap_imp.values,color=[DOM_COL.get(classify(v),C['grey']) for v in shap_imp.index],width=0.8,alpha=0.5)
ax2t=ax2_.twinx()
ax2t.plot(range(1,len(shap_imp)+1),cum_imp*100,'o-',color=C['red'],lw=2,ms=2)
ax2t.axhline(y=80,color=C['green'],ls='--',lw=1)
ax2_.set_xlabel('Feature Rank'); ax2_.set_ylabel('|SHAP|')
ax2t.set_ylabel('Cumulative %',color=C['red']); ax2t.tick_params(axis='y',labelcolor=C['red'])
ax2_.set_title(f'C. Cumulative SHAP\nTop {n_80} = 80%',fontweight='bold',loc='left',fontsize=11)

ax3_=fig4.add_subplot(gs4[1,:2])
top15_shap=shap_vals[:,[feature_cols.index(v) for v in ranking.head(15)['Variable']]]
bp=ax3_.boxplot([top15_shap[:,i] for i in range(15)],tick_labels=ranking.head(15)['Variable'].tolist(),
                patch_artist=True,vert=False,widths=0.6,
                flierprops={'markersize':2,'alpha':0.3},medianprops={'color':'red','linewidth':1.5})
for patch in bp['boxes']: patch.set_facecolor(C['blue']); patch.set_alpha(0.3)
ax3_.set_xlabel('SHAP Value'); ax3_.set_title('D. SHAP Distribution (Top-15)',fontweight='bold',loc='left',fontsize=11)
ax3_.axvline(x=0,color=C['grey'],ls='-',lw=0.8)

ax4_=fig4.add_subplot(gs4[1,2]); ax4_.axis('off')
lines=[("MODELING SUMMARY",C['blue'],13,True),("",C['grey'],8,False),
    (f"XGBoost CV R² = {results['XGBoost']['r2_mean']:.3f}±{results['XGBoost']['r2_std']:.3f}",C['green'],10,True),
    (f"LightGBM CV R² = {results['LightGBM']['r2_mean']:.3f}±{results['LightGBM']['r2_std']:.3f}",C['green'],10,True),
    (f"RF CV R² = {results['RF']['r2_mean']:.3f}±{results['RF']['r2_std']:.3f}",C['orange'],10,True),
    ("",C['grey'],8,False),
    (f"Boruta: {n_conf} confirmed / {len(feature_cols)}",C['purple'],10,True),
    (f"Recommended: {len(union_vars)} vars",C['red'],10,True),
    ("Domain breakdown:",C['teal'],10,True)]
for d in ['Climate','Soil','Topography']:
    lines.append((f"  {d}: {sum(1 for v in union_vars if classify(v)==d)} vars",DOM_COL.get(d,C['grey']),9,False))
lines.append(("",C['grey'],8,False))
lines.append(("Yield: County Bayesian Ensemble",C['grey'],9,False))
lines.append((f"  Prior: 6.00 t/ha (Beijing stats)",C['grey'],9,False))
for i,(text,color,size,bold) in enumerate(lines):
    ax4_.text(0.05,0.97-i*0.036,text,transform=ax4_.transAxes,fontsize=size,fontweight='bold' if bold else 'normal',color=color)
ax4_.set_title('E. Summary',fontweight='bold',loc='left',fontsize=11)
fig4.savefig(os.path.join(OUT_MAIN,'fig04_feature_selection_dashboard.png'),dpi=600,facecolor='white')
fig4.savefig(os.path.join(OUT_MAIN,'fig04_feature_selection_dashboard.tiff'),dpi=600,facecolor='white',pil_kwargs={'compression':'lzw'})
plt.close(); print("    fig04_feature_selection_dashboard", flush=True)

# ────────────────────────────────────────────
# 10. SUPP: SHAP DEPENDENCE
# ────────────────────────────────────────────
top3=ranking.head(3)['Variable'].tolist()
fig_s,axes_s=plt.subplots(1,3,figsize=(18,5))
for i,feat in enumerate(top3):
    idx=feature_cols.index(feat)
    sv=shap_vals[:,idx]; fv=X[:,idx]
    cf=ranking.head(5).iloc[min(i+1,4)]['Variable']
    if cf==feat: cf=ranking.head(5).iloc[0]['Variable']
    ci=feature_cols.index(cf)
    sc=axes_s[i].scatter(fv,sv,c=X[:,ci],cmap='coolwarm',s=15,alpha=0.6)
    axes_s[i].set_xlabel(feat); axes_s[i].set_ylabel(f'SHAP({feat})')
    axes_s[i].set_title(f'{feat}\ncolored by {cf}',fontsize=10)
    cbar=plt.colorbar(sc,ax=axes_s[i]); cbar.set_label(cf,fontsize=8)
fig_s.savefig(os.path.join(OUT_SUPP,'fig_s1_shap_dependence.png'),dpi=300,facecolor='white')
plt.close(); print("    fig_s1_shap_dependence", flush=True)

# ────────────────────────────────────────────
# 11. SAVE BEST MODEL
# ────────────────────────────────────────────
final_model = models[best_model]
final_model.fit(X, y)
if hasattr(final_model,'save_model'):
    final_model.save_model(os.path.join(OUT_MODELS,f'{best_model.lower()}_ensemble_final.json'))
print(f"[8] Best model saved: {best_model}", flush=True)

# ────────────────────────────────────────────
# DONE
# ────────────────────────────────────────────
print(f"\n{'='*60}", flush=True)
print(f"REBUILD COMPLETE", flush=True)
print(f"{'='*60}", flush=True)
print(f"""
Key Results (County-Yield Ensemble):
  XGBoost  CV R² = {results['XGBoost']['r2_mean']:.4f} ± {results['XGBoost']['r2_std']:.4f}
  LightGBM CV R² = {results['LightGBM']['r2_mean']:.4f} ± {results['LightGBM']['r2_std']:.4f}
  RF       CV R² = {results['RF']['r2_mean']:.4f} ± {results['RF']['r2_std']:.4f}

  Boruta: {n_conf}/{len(feature_cols)} confirmed, {n_rej} rejected
  Recommended: {len(union_vars)} variables

  Top-10 features:
""" + '\n'.join([f'    {i+1:2d}. [{classify(r.Variable):8s}] {r.Variable:25s} |SHAP|={r.SHAP_Importance:.4f}' for i,(_,r) in enumerate(ranking.head(10).iterrows())]))
