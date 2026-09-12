"""QA-06 v3: Feature Selection with County-Yield Ensemble results"""
import pandas as pd, numpy as np, os, warnings
warnings.filterwarnings('ignore')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch

ROOT = r'D:\2026-SP'
OUT_QA = os.path.join(ROOT, 'Outputs', 'figures', 'qa')
os.makedirs(OUT_QA, exist_ok=True)

C = {'blue':'#2F5496','red':'#c5221f','orange':'#e37400','green':'#1b8a4a',
     'grey':'#8c8c8c','purple':'#6a0dad','teal':'#008080'}
DOM_COL = {'Climate': C['blue'], 'Soil': C['orange'], 'Topography': C['green']}

ranking = pd.read_csv(os.path.join(ROOT, 'Outputs', 'intermediate', 'feature_ranking_full.csv'))
boruta = pd.read_csv(os.path.join(ROOT, 'Outputs', 'intermediate', 'boruta_results.csv'))
domain_sum = pd.read_csv(os.path.join(ROOT, 'Outputs', 'intermediate', 'domain_summary.csv')).set_index('Domain')

n_conf = (boruta['Class'] == 'Confirmed').sum()
n_rej = (boruta['Class'] == 'Rejected').sum()

fig6, axes6 = plt.subplots(2, 2, figsize=(16, 12))

# A: SHAP top-25
ax_a6 = axes6[0,0]
top25 = ranking.head(25).sort_values('SHAP_Importance', ascending=True)
colors_a = [DOM_COL.get(d, C['grey']) for d in top25['Domain']]
ax_a6.barh(range(len(top25)), top25['SHAP_Importance'].values, color=colors_a, height=0.7)
for i, (v, cls) in enumerate(zip(top25['Variable'], top25['Boruta_Class'])):
    if cls == 'Confirmed':
        ax_a6.text(top25['SHAP_Importance'].values[i] + 0.001, i, 'v', fontsize=8, color=C['green'], fontweight='bold', va='center')
ax_a6.set_yticks(range(len(top25)))
ax_a6.set_yticklabels(top25['Variable'], fontsize=7.5)
ax_a6.set_xlabel('mean(|SHAP|)')
ax_a6.set_title('A. SHAP Feature Importance (Top-25)\nEnsemble yield, 234 grids (only 4 Boruta confirmed)',
               fontweight='bold', loc='left', fontsize=10)
ax_a6.legend(handles=[Patch(color=c, label=d) for d,c in DOM_COL.items()], fontsize=8, loc='lower right')

# B: Boruta results
ax_b6 = axes6[0,1]
ax_b6.pie([n_conf, n_rej], labels=['Confirmed (%d vars)' % n_conf, 'Rejected (%d vars)' % n_rej],
         colors=[C['green'], C['red']], autopct='%1.1f%%',
         textprops={'fontsize':11}, startangle=90, explode=[0.03, 0.03])
ax_b6.set_title('B. Boruta Feature Selection\n(50 iterations, RF learner, Ensemble yield)',
               fontweight='bold', loc='left', fontsize=10)

# C: Domain summary
ax_c6 = axes6[1,0]
doms = list(domain_sum.index)
x_c = np.arange(len(doms))
ax_c6.bar(x_c - 0.2, domain_sum['N_Vars'], 0.4, color=C['blue'], alpha=0.5, label='Total variables')
ax_c6.bar(x_c + 0.2, domain_sum['N_Confirmed'], 0.4, color=C['green'], alpha=0.7, label='Boruta confirmed')
# Add mean SHAP as line
ax_c6r = ax_c6.twinx()
ax_c6r.plot(x_c, domain_sum['Mean_SHAP'], 'o-', color=C['red'], lw=2, ms=8)
ax_c6r.set_ylabel('Mean |SHAP|', color=C['red'])
ax_c6.set_xticks(x_c)
ax_c6.set_xticklabels(doms, rotation=30, ha='right', fontsize=9)
ax_c6.set_ylabel('Count')
ax_c6.set_title('C. Domain Summary: Count vs Importance\n(Climate dominates; soil contributes despite few vars)',
               fontweight='bold', loc='left', fontsize=10)
ax_c6.legend(fontsize=8, loc='upper left')

# D: Summary card
ax_d6 = axes6[1,1]
ax_d6.axis('off')

# Compute union
bor_conf = ranking[ranking['Boruta_Class'] == 'Confirmed']['Variable'].tolist()
cum_imp = np.cumsum(ranking['SHAP_Importance'].values) / ranking['SHAP_Importance'].values.sum()
n_80 = np.searchsorted(cum_imp, 0.80) + 1
shap_top = ranking.head(n_80)['Variable'].tolist()
union = list(dict.fromkeys(bor_conf + shap_top))

lines = [
    ("FEATURE SELECTION SUMMARY", C['blue'], 13, True),
    (" ", C['grey'], 8, False),
    ("Method: Boruta + SHAP on Ensemble Yield", C['purple'], 10, True),
    (" ", C['grey'], 8, False),
    ("Boruta confirmed: %d vars" % n_conf, C['green'], 10, True),
    ("  (bio9, tavg_12, bio1, bio11 only)", C['grey'], 9, False),
    ("SHAP 80%% cumulative: top %d vars" % n_80, C['blue'], 10, True),
    ("UNION total: %d vars" % len(union), C['red'], 11, True),
    (" ", C['grey'], 8, False),
    ("Domain breakdown:", C['orange'], 10, True),
]
def classify_simple(v):
    if v in ('clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','ph','nitrogen_cgkg'):
        return 'Soil'
    if v in ('elevation_m','slope_deg','aspect_deg'):
        return 'Topography'
    return 'Climate'
for d in ['Climate', 'Soil', 'Topography']:
    cnt = sum(1 for v in union if classify_simple(v) == d)
    lines.append(("  %s: %d vars" % (d, cnt), DOM_COL.get(d, C['grey']), 9, False))
lines += [
    (" ", C['grey'], 8, False),
    ("CRITICAL FINDINGS", C['red'], 10, True),
    ("  4/71 Boruta confirmed (vs 33 in Ridge v1)", C['red'], 8, False),
    ("  Yield variance 0.35 >> real signal sparse", C['red'], 8, False),
    ("  Top2 = winter temp (bio9, tavg_12)", C['teal'], 8, False),
    ("  Soil soc_dgkg enters top-5 for first time", C['green'], 8, False),
    (" ", C['grey'], 8, False),
    ("OVERALL: C+ (limited by yield signal)", C['teal'], 10, True),
    ("  Rerun with APSIM/denser yield when available", C['teal'], 8, False),
]
for i, (text, color, size, bold) in enumerate(lines):
    ax_d6.text(0.05, 0.97 - i*0.027, text, transform=ax_d6.transAxes,
               fontsize=size, fontweight='bold' if bold else 'normal', color=color)
ax_d6.set_title('D. Feature Selection Summary (Ensemble)', fontweight='bold', loc='left', fontsize=11)

fig6.suptitle('Figure QA-6: Feature Importance & Selection (County-Yield Ensemble)', fontsize=16, fontweight='bold', y=1.02)
fig6.savefig(os.path.join(OUT_QA, 'qa06_feature_selection.png'), dpi=300, facecolor='white')
plt.close(fig6)
print("qa06 Done!")
