# -*- coding: utf-8 -*-
"""W19: External validation of the audit framework on the full Xiao2024 (2024
Nature Food) North China Plain History panel — the reviewer-suggested
"more complete published data" test.

Logic: same framework (XGBoost + random/block CV, same feature family) that
shows R2≈0 on the 43-grid Pinggu baseline target must recover strong signal on
a dataset spanning real environmental gradients — otherwise the framework
destroys signal (reviewer's "overfitting" concern); if it does recover signal,
the Pinggu null is a *detectability* outcome of a small, low-variance domain,
not evidence against environmental control of yield.

Steps
  1. Extract History rows from Allregions.rds (NCP extent 112.1-123.1E,
     29.7-40.7N; gridcell -> row-major 0.008333 deg, NCOL=1320).
  2. Aggregate Yield to the SAME 0.0417-deg lattice as the diagnostic line.
  3. Sample features: WorldClim 19 bio (global 2.5min rasters) + SoilGrids
     topsoil 8 (global 5 km). SRTM is Pinggu-only -> terrain omitted here,
     declared in methods.
  4. CV: random 5-fold x3 seeds + checkerboard 1x-range + latitude blocks.
  5. Scale-stratified experiment: subsample domains of increasing
     environmental spread (bio1 SD) to show detectability scales with
     environmental variance, reconciling "environment matters" (large
     gradients) with "no detectable signal" (small low-variance domains).
Outputs: Outputs/intermediate/w19_external_validation.csv,
         w19_scale_gradient.csv, w19_national_grid_features.csv (persisted).
"""
import os, warnings
import numpy as np
import pandas as pd
import rasterio
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)
RES = 0.041666666666666664  # same lattice as diagnostic line

# ---------- 1. History panel ----------
FPATH = os.path.join(INT, "w19_national_grid_features.csv")
if os.path.exists(FPATH):
    print("[0] loading persisted feature table ...", flush=True)
    F = pd.read_csv(FPATH)
else:
  print("[1] reading rds ...", flush=True)
  import pyreadr
  df = list(pyreadr.read_r(os.path.join(ROOT, "Data", "Management", "Xiao2024", "Allregions.rds")).values())[0]
  h = df[df["Period"] == "History"][["gridcell", "Yield"]].copy()
  del df
  print(f"    History rows: {len(h):,}", flush=True)

  LON0, LAT1, RES1, NCOL = 112.1, 40.7, 0.008333333333333333, 1320
  g = h["gridcell"].values
  lon = LON0 + (g % NCOL) * RES1
  lat = LAT1 - (g // NCOL) * RES1
  h["lon"] = lon; h["lat"] = lat

  # ---------- 2. aggregate to 0.0417 lattice ----------
  print("[2] aggregating to 0.0417-deg lattice ...", flush=True)
  h["glon"] = np.round((h["lon"] - 112.0) / RES).astype(int)
  h["glat"] = np.round((40.7 - h["lat"]) / RES).astype(int)
  agg = h.groupby(["glon", "glat"])["Yield"].agg(["mean", "std", "count"]).reset_index()
  agg = agg[(agg["count"] >= 25)]  # >=25 of ~64 fine cells per coarse cell
  agg["lon"] = 112.0 + agg["glon"] * RES
  agg["lat"] = 40.7 - agg["glat"] * RES
  print(f"    coarse grids: {len(agg):,} (yield mean {agg['mean'].mean():.2f}, SD {agg['mean'].std():.2f})", flush=True)

# ---------- 3. features ----------
if not os.path.exists(FPATH):
    print("[3] sampling WorldClim + SoilGrids ...", flush=True)
    BIO = [f"wc2.1_2.5m_bio_{i}" for i in range(1, 20)]
    SOIL = ["clay", "sand", "soc", "bdod", "cec", "phh2o", "nitrogen"]
    soil_dir = os.path.join(ROOT, "Data", "SoilGrids_wgs84")
    soil_t = []
    for v in SOIL:
        cands = [os.path.join(soil_dir, f) for f in os.listdir(soil_dir) if f.startswith(v + "_0-5cm")]
        soil_t += cands[:1]
    from rasterio.warp import transform as warp_transform
    def sample_batch(tifs, lons, lats):
        """Batch-sample rasters; transform lon/lat -> raster CRS (SoilGrids files
        are ESRI:54052 metric despite the folder name); nodata -> NaN."""
        out = np.full((len(lons), len(tifs)), np.nan, dtype=np.float32)
        for j, p in enumerate(tifs):
            try:
                with rasterio.open(p) as s:
                    xs, ys = lons, lats
                    if s.crs and s.crs.to_string() not in ("EPSG:4326", "WGS 84"):
                        xs, ys = warp_transform("EPSG:4326", s.crs, list(lons), list(lats))
                    pts = [(float(x), float(y)) for x, y in zip(xs, ys)]
                    vals = np.array([r[0] for r in s.sample(pts)], dtype=np.float64)
                    if s.nodata is not None:
                        vals[vals == s.nodata] = np.nan
                    out[:, j] = vals
            except Exception as e:
                print(f"    [warn] {os.path.basename(p)} unreadable ({type(e).__name__}), skipped", flush=True)
        return out
    bio_t = [os.path.join(ROOT, "Data", "WorldClim", f"{b}.tif") for b in BIO]
    Xbio = sample_batch(bio_t, agg["lon"].values, agg["lat"].values)
    Xsoil = sample_batch(soil_t, agg["lon"].values, agg["lat"].values)
    cols = BIO + [os.path.basename(p).split("_0-5cm")[0] for p in soil_t]
    F = pd.DataFrame(np.hstack([Xbio, Xsoil]), columns=cols)
    F["lon"], F["lat"], F["y"] = agg["lon"].values, agg["lat"].values, agg["mean"].values
    F = F.dropna(axis=1, how="all").dropna(axis=0, how="any")  # nitrogen raster is corrupt -> all-NaN column
    print(f"    grids with complete features: {len(F):,} (features kept: {len(F.columns)-3})", flush=True)
    F.to_csv(os.path.join(INT, "w19_national_grid_features.csv"), index=False)

# ---------- 4. CV on the full gradient ----------
print("[4] CV on full NCP gradient ...", flush=True)
FEATS = [c for c in F.columns if c not in ("lon", "lat", "y")]
X = F[FEATS].values.astype(float); y = F["y"].values.astype(float)
coords = F[["lon", "lat"]].values
rng = np.random.default_rng(0)
def cv_random(n):
    return [list(KFold(5, shuffle=True, random_state=s).split(np.zeros((n, 1)))) for s in SEEDS]
def cv_checker(coords, edge_deg):
    key = (np.floor(coords[:, 0] / edge_deg).astype(int) + 2 * np.floor(coords[:, 1] / edge_deg).astype(int)) % 2
    return [[(np.where(key != k)[0], np.where(key == k)[0]) for k in (0, 1)]] * 3
def cv_lat(coords):
    b = pd.qcut(coords[:, 1], 5, labels=False)
    return [[(np.where(b != k)[0], np.where(b == k)[0]) for k in np.unique(b)]] * 3
def run(splits, tag):
    ps = []
    for sp, s in zip(splits, SEEDS):
        yp = np.zeros(len(y))
        for tr, te in sp:
            m = XGBRegressor(**NEW).fit(X[tr], y[tr]); yp[te] = m.predict(X[te])
        ps.append(r2_score(y, yp))
    print(f"    {tag}: pooled {np.mean(ps):.4f} +- {np.std(ps):.4f}", flush=True)
    return np.mean(ps), np.std(ps), ps
rows = []
for tag, sp in [("random", cv_random(len(y))),
                ("checker_1x", cv_checker(coords, 0.10)),
                ("lat_block5", cv_lat(coords))]:
    m, sd, ps = run(sp, tag)
    rows.append({"dataset": "NCP_national", "scheme": tag, "n": len(y),
                 "y_sd": round(float(y.std()), 3), "pooled_mean": round(m, 4),
                 "pooled_std": round(sd, 4), "by_seed": [round(p, 4) for p in ps]})

# ---------- 5. scale-stratified detectability ----------
print("[5] scale-stratified detectability ...", flush=True)
# bin grids by local bio1 (annual mean temperature); take increasingly narrow
# latitude bands -> decreasing environmental spread, mirroring Pinggu's narrow domain
F2 = F.sort_values("lat").reset_index(drop=True)
bands = [(31.5, 40.5, "full_gradient"), (35.0, 40.5, "north_half"),
         (37.5, 40.5, "northern_quarter"), (39.3, 40.5, "pinggu_like_band")]
for lo, hi, name in bands:
    sub = F2[(F2["lat"] >= lo) & (F2["lat"] <= hi)]
    if len(sub) < 400:
        print(f"    {name}: skipped (n={len(sub)})", flush=True); continue
    sub = sub.sample(min(len(sub), 6000), random_state=7)
    Xs = sub[FEATS].values.astype(float); ys = sub["y"].values.astype(float)
    cs = sub[["lon", "lat"]].values
    env_sd = float(sub["wc2.1_2.5m_bio_1"].std())
    sp = cv_random(len(ys))
    ps = []
    for splits, s in zip(sp, SEEDS):
        yp = np.zeros(len(ys))
        for tr, te in splits:
            m2 = XGBRegressor(**NEW).fit(Xs[tr], ys[tr]); yp[te] = m2.predict(Xs[te])
        ps.append(r2_score(ys, yp))
    print(f"    {name}: n={len(sub)} bio1_sd={env_sd:.2f}C pooled={np.mean(ps):.4f}", flush=True)
    rows.append({"dataset": name, "scheme": "random", "n": len(sub),
                 "y_sd": round(float(ys.std()), 3), "env_bio1_sd": round(env_sd, 2),
                 "pooled_mean": round(float(np.mean(ps)), 4),
                 "pooled_std": round(float(np.std(ps)), 4), "by_seed": [round(p, 4) for p in ps]})
pd.DataFrame(rows).to_csv(os.path.join(INT, "w19_external_validation.csv"), index=False, encoding="utf-8-sig")
print("W19 done")
