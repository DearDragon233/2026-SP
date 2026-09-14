# -*- coding: utf-8 -*-
"""P6: 复现包兑现（W11 承诺，W16 变现）——
1. 固定折划分文件：random(5 seeds)/lat4/checker_1x 三套 fold_assignments
2. 依赖清单 requirements.txt
输出: Outputs/repro_package/fold_assignments_*.csv + requirements.txt
"""
import pandas as pd, numpy as np, os, json, sklearn, xgboost
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

ROOT = r"D:\2026-SP"
RP = os.path.join(ROOT, "Outputs", "repro_package")
os.makedirs(RP, exist_ok=True)
df = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "data_with_yield_ensemble.csv"))
coords = df[["lon", "lat"]].values
KM_LON = 111.32 * np.cos(np.radians(40.2)); RANGE = 4.62
SEEDS = [7, 21, 42, 123, 2026]
grid_id = np.arange(len(df))

# random 5-fold × 5 seeds
rows = []
for s in SEEDS:
    for fold, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=s).split(grid_id)):
        for g in te:
            rows.append({"seed": s, "fold": fold, "grid_id": g})
pd.DataFrame(rows).to_csv(os.path.join(RP, "fold_assignments_random.csv"), index=False)

# lat4（块划分固定，种子无关）
latq = np.asarray(pd.qcut(coords[:, 1], 4, labels=False))
pd.DataFrame({"grid_id": grid_id, "block": latq}).to_csv(os.path.join(RP, "fold_assignments_lat4.csv"), index=False)

# checker 1×（主口径）
gl = np.floor(coords[:, 0] / (RANGE / KM_LON)).astype(int)
ga = np.floor(coords[:, 1] / (RANGE / 110.57)).astype(int)
pd.DataFrame({"grid_id": grid_id, "block": (gl + ga) % 2}).to_csv(
    os.path.join(RP, "fold_assignments_checker1x.csv"), index=False)

# LOBO8 / 环境空间 KMeans4
from sklearn.cluster import KMeans
blk8 = KMeans(8, random_state=42, n_init=10).fit_predict(coords)
pd.DataFrame({"grid_id": grid_id, "block": blk8}).to_csv(os.path.join(RP, "fold_assignments_lobo8.csv"), index=False)
drop = {"lon", "lat", "wheat_yield_tha", "wheat_yield_pred_tha", "yield_uncertainty_tha",
        "yield_source", "yield_blended_tha", "yield_source_blend"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64", "int64")]
Xf = StandardScaler().fit_transform(np.nan_to_num(df[FEATS].values.astype(float), nan=0.0))
blkE = KMeans(4, random_state=42, n_init=10).fit_predict(Xf)
pd.DataFrame({"grid_id": grid_id, "block": blkE}).to_csv(os.path.join(RP, "fold_assignments_envkmeans4.csv"), index=False)

# requirements.txt
lines = [
    "# 2026-SP reproducibility package (W16-P6)",
    "# Python 3.13 (D:\\PythonAbout\\python.exe)",
    f"scikit-learn=={sklearn.__version__}",
    f"xgboost=={xgboost.__version__}",
    "pandas>=2.0", "numpy>=1.26", "scipy>=1.11",
    "lightgbm>=4.0", "quantile-forest>=1.3", "shap>=0.44",
    "rasterio>=1.3", "matplotlib>=3.8", "optuna>=3.4",
    "# seeds used: 7/21/42/123/2026 (5-seed) and subsets (7/21/42 = 3-seed canonical)",
]
open(os.path.join(RP, "requirements.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("repro package:", sorted(os.listdir(RP)))
