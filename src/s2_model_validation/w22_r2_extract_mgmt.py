# -*- coding: utf-8 -*-
"""W22-R2: extract management columns + three-period yields from Allregions.rds
in ONE pass; aggregate to the W19 0.0417-deg national lattice; merge with the
persisted environmental features. Also: Pinggu 43-grid management columns via
nearest-neighbour snap from xiao2024_rds_pinggu_raw.csv (History rows).
Outputs: w22_r2_national_EMM.csv, w22_r2_pinggu43_mgmt.csv"""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from scipy.spatial import cKDTree

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
RES = 0.041666666666666664
MGMT = ["WN", "WR", "xWIrri", "MN", "MR", "xMIrri"]

import pyreadr
print("[R2] reading rds (single pass) ...", flush=True)
df = list(pyreadr.read_r(os.path.join(ROOT, "Data", "Management", "Xiao2024", "Allregions.rds")).values())[0]
keep = ["gridcell", "Period", "SSP"] + MGMT + ["Yield", "New_Yield"]
h = df[keep].copy(); del df

LON0, LAT1, RES1, NCOL = 112.1, 40.7, 0.008333333333333333, 1320
g = h["gridcell"].values
h["lon"] = LON0 + (g % NCOL) * RES1
h["lat"] = LAT1 - (g // NCOL) * RES1
h["glon"] = np.round((h["lon"] - 112.0) / RES).astype(int)
h["glat"] = np.round((40.7 - h["lat"]) / RES).astype(int)
cnt = h.groupby(["glon", "glat"]).size().rename("n_fine")
# management: mean over ALL rows per cell (reference management surface)
mg = h.groupby(["glon", "glat"])[MGMT].mean().reset_index()
mg = mg.join(cnt, on=["glon", "glat"])
mg = mg[mg.n_fine >= 50].drop(columns=["n_fine"])   # >=50 fine rows (of ~384 = 64x3periods x2ssp)
# yields per Period (mean across SSP/GCM) + per SSP for scenarios
yp = h.groupby(["glon", "glat", "Period"])["Yield"].mean().unstack("Period").reset_index()
ys = h[h.Period != "History"].groupby(["glon", "glat", "SSP"])["Yield"].mean().unstack("SSP").reset_index()
L = mg.merge(yp, on=["glon", "glat"], how="inner").merge(ys, on=["glon", "glat"], how="left")
L["lon"] = 112.0 + L["glon"] * RES; L["lat"] = 40.7 - L["glat"] * RES

E = pd.read_csv(os.path.join(INT, "w19_national_grid_features.csv"))
key = lambda d: (d["lon"].round(5).astype(str) + "_" + d["lat"].round(5).astype(str))
E["_k"] = key(E); L["_k"] = key(L)
M = E.merge(L.drop(columns=["glon", "glat", "lon", "lat"]), on="_k", how="inner").drop(columns=["_k"])
print(f"[R2] national E+M+periods table: {len(M)} grids | mgmt NaN: {int(M[MGMT].isna().any(axis=1).sum())}", flush=True)
M.to_csv(os.path.join(INT, "w22_r2_national_EMM.csv"), index=False)

# Pinggu 43: snap History management from the raw pinggu panel
P = pd.read_csv(os.path.join(INT, "xiao2024_rds_pinggu_raw.csv"))
Ph = P[P.Period == "History"]
E234 = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
mA = E234["wheat_yield_tha"].notna().values
A = E234[mA][["lon", "lat"]].copy()
tree = cKDTree(Ph[["lon", "lat"]].values)
dd, nn = tree.query(A[["lon", "lat"]].values, k=1)
for c in MGMT:
    A[c] = Ph[c].values[nn]
A["snap_km"] = dd * 111.32 * np.cos(np.radians(40.2))
A.to_csv(os.path.join(INT, "w22_r2_pinggu43_mgmt.csv"), index=False)
print(f"[R2] Pinggu43 mgmt: n={len(A)}, snap max {A.snap_km.max():.2f} km, median {A.snap_km.median():.2f} km", flush=True)
print("[R2] period yield means:", {p: round(float(M[p].mean()), 2) for p in ["History", "2030s", "2060s"] if p in M}, flush=True)
print("R2 done")
