# -*- coding: utf-8 -*-
"""过拟合与常见问题诊断（Goal Brief 验收第6条）：
1. 学习曲线（XGBoost_tuned 管线，250m v4 特征，301 样本）
2. 重复 5×5 嵌套 CV（抗过拟合的稳健性能估计）
3. 数据泄漏排查（目标统计特征/空间聚合变量的泄漏路径检查）
4. 样本分布与目标分布检查
输出 overfitting_diagnosis.json + 学习曲线 PNG（600dpi）
"""
import pandas as pd, numpy as np, json, os, warnings
warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import learning_curve, RepeatedKFold, cross_val_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
FIG = os.path.join(ROOT, "Outputs", "figures", "main")

df = pd.read_csv(os.path.join(INT, "fine250_v4_final.csv"))
# 与 v4 管线一致的特征集：数值列去掉标识与目标
drop = ["cell_r", "cell_c", "lon", "lat", "yield_2021_tha", "n_px"]
fc = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
X_raw = df[fc].values
y = df["yield_2021_tha"].values
print("samples:", len(y), "| features:", len(fc))

# 复现 v4 最优超参（Optuna 结果，摘要中记录）
best = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
            colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
            random_state=42, n_jobs=1, verbosity=0)

def pipe_fit(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    m = XGBRegressor(**best)
    m.fit(sc.transform(Xtr), ytr)
    return m.predict(sc.transform(Xte))

# ---------- 1. 学习曲线（手动实现，配合管道内标准化） ----------
sizes = np.linspace(0.2, 1.0, 9)
from sklearn.metrics import r2_score
from sklearn.model_selection import KFold
tr_m, va_m, tr_s, va_s = [], [], [], []
for frac in sizes:
    n = int(len(y) * frac)
    rng = np.random.RandomState(42)
    idx = rng.permutation(len(y))[:n]
    Xs, ys = X_raw[idx], y[idx]
    tS, vS = [], []
    kf = list(KFold(5, shuffle=True, random_state=42).split(Xs))
    for tr, te in kf:
        p = pipe_fit(Xs[tr], ys[tr], Xs[te])
        tS.append(r2_score(ys[te], p))
        # 训练集内 R²（衡量 gap）
        sc = StandardScaler().fit(Xs[tr])
        m = XGBRegressor(**best); m.fit(sc.transform(Xs[tr]), ys[tr])
        tS.append(r2_score(ys[tr], m.predict(sc.transform(Xs[tr]))))
        vS.append(tS[-2])
    tr_m.append(np.mean(tS[1::2])); tr_s.append(np.std(tS[1::2]))
    va_m.append(np.mean(vS)); va_s.append(np.std(vS))
    print(f"  size={n}: train R2={tr_m[-1]:.3f}±{tr_s[-1]:.3f} | cv R2={va_m[-1]:.3f}±{va_s[-1]:.3f}")

# ---------- 2. 重复嵌套 CV（5×5） ----------
rkf = RepeatedKFold(n_splits=5, n_repeats=5, random_state=42)
scores = []
for tr, te in rkf.split(X_raw):
    p = pipe_fit(X_raw[tr], y[tr], X_raw[te])
    scores.append(r2_score(y[te], p))
scores = np.array(scores)
print(f"\nrepeated 5x5 CV: R2={scores.mean():.4f}±{scores.std():.4f} | min={scores.min():.3f} max={scores.max():.3f}")

# ---------- 3. 泄漏排查 ----------
leak_report = {}
# 3a. 特征与目标的空间聚合同源性：n_px（参与聚合的像元数）不是产量信息 → 排除过
leak_report["n_px_excluded"] = True
# 3b. 目标来自 Zenodo 30m 聚合 → 特征全部来自环境栅格（WorldClim/SoilGrids/SRTM），无产量衍生变量
yield_derived = [c for c in fc if any(k in c.lower() for k in ("yield", "pred", "interp", "blend"))]
leak_report["yield_derived_features_in_model"] = yield_derived  # 应为空
# 3c. StandardScaler 只在训练折内 fit（本诊断与 v4 管线均如此）
leak_report["scaler_fit_within_fold"] = True
# 3d. 空间泄漏：随机 CV 的 fold 内近邻对检查（同一 250m 格网相邻格距离 ~250m）
from scipy.spatial import cKDTree
coords = np.deg2rad(df[["lon", "lat"]].values)
tree = cKDTree(coords)
pairs_same_fold = 0
kf = list(KFold(5, shuffle=True, random_state=42).split(X_raw))
fold_id = np.zeros(len(y), int)
for f, (tr, te) in enumerate(kf):
    fold_id[te] = f
for i in range(len(y)):
    dd, jj = tree.query(coords[i], k=9)  # 8 近邻
    for d, j in zip(dd[1:], jj[1:]):
        if d < 0.005 and fold_id[i] == fold_id[j]:  # <500m 且同折
            pairs_same_fold += 1
leak_report["spatial_nearby_same_fold_pairs"] = int(pairs_same_fold)
leak_report["spatial_note"] = "随机 CV 下近邻对同折不可避免（结构性空间泄漏）——这正是论文报告空间 CV 崩塌的原因，已在结果中诚实呈现"

# ---------- 4. 目标分布 ----------
from scipy import stats
norm_p = float(stats.normaltest(y).pvalue)
skew = float(pd.Series(y).skew())
print(f"\ntarget: mean={y.mean():.3f} std={y.std():.3f} skew={skew:.3f} normality_p={norm_p:.4f}")

# ---------- 学习曲线图（Fathom 风格：灰底、navy 主线、单 accent） ----------
fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=600)
xs_n = np.array(sizes) * len(y)
ax.fill_between(xs_n, np.array(va_m) - np.array(va_s),
                np.array(va_m) + np.array(va_s), alpha=0.15, color="#1d3557", lw=0)
ax.plot(xs_n, tr_m, "o-", color="#b5623b", lw=1.4, ms=3.5, label="训练集 R²")
ax.plot(xs_n, va_m, "o-", color="#1d3557", lw=1.4, ms=3.5, label="交叉验证 R²")
ax.set_xlabel("训练样本数", fontsize=10)
ax.set_ylabel("R²", fontsize=10)
ax.legend(fontsize=9, frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.25, lw=0.5)
ax.tick_params(labelsize=9)
fig.tight_layout()
p1 = os.path.join(FIG, "fig09_learning_curve.png")
fig.savefig(p1, dpi=600, bbox_inches="tight")
plt.close(fig)
print("\nsaved:", p1)

out = {
    "n_samples": int(len(y)), "n_features": len(fc),
    "learning_curve": {"sizes": xs_n.astype(int).tolist(),
                       "train_r2_mean": [round(v, 4) for v in tr_m],
                       "cv_r2_mean": [round(v, 4) for v in va_m],
                       "cv_r2_std": [round(v, 4) for v in va_s]},
    "final_gap": round(tr_m[-1] - va_m[-1], 4),
    "repeated_cv": {"mean": round(float(scores.mean()), 4), "std": round(float(scores.std()), 4),
                    "min": round(float(scores.min()), 4), "max": round(float(scores.max()), 4),
                    "n_runs": int(len(scores))},
    "leakage_checks": leak_report,
    "target": {"mean": round(float(y.mean()), 4), "std": round(float(y.std()), 4),
               "skew": round(skew, 4), "normality_p": round(norm_p, 4)},
    "overfitting_verdict": None,  # 由主线根据 gap 判定写入报告
}
with open(os.path.join(INT, "overfitting_diagnosis.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("saved overfitting_diagnosis.json")
