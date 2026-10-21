# -*- coding: utf-8 -*-
"""W25-R2: extract the RS-derived actual-yield target (ChinaWheatYield30m 2021)
at the NCP national lattice (7,107 cells from w22_r2_national_EMM.csv).
Windowed sampling: 3x3 30m-pixel mean at each lattice centre; n_px = valid count.
Output: w25_r2_national_rs_target.csv"""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import rasterio

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
M = pd.read_csv(os.path.join(INT, "w22_r2_national_EMM.csv"))
P = os.path.join(ROOT, "Data", "2021ChinaWheatYield30m.tif")

vals = np.full(len(M), np.nan); npx = np.zeros(len(M), int)
with rasterio.open(P) as src:
    tr = src.transform
    for i, (lo, la) in enumerate(zip(M.lon.values, M.lat.values)):
        try:
            r0, c0 = rasterio.transform.rowcol(tr, lo - 0.0009, la + 0.0009)  # ~2x2 px window (30m px)
            r1, c1 = rasterio.transform.rowcol(tr, lo + 0.0009, la - 0.0009)
            r0, r1 = max(0, min(r0, src.height - 1)), max(0, min(r1, src.height - 1))
            c0, c1 = max(0, min(c0, src.width - 1)), max(0, min(c1, src.width - 1))
            if r1 <= r0 or c1 <= c0:
                continue
            w = rasterio.windows.Window(c0, r0, c1 - c0 + 1, r1 - r0 + 1)
            sub = src.read(1, window=w)
            m = sub > 0
            npx[i] = int(m.sum())
            if m.sum() >= 2:
                vals[i] = float(sub[m].mean()) / 1000.0
        except Exception:
            pass
        if (i + 1) % 1000 == 0:
            print(f"  {i+1}/{len(M)}", flush=True)

out = M[["lon", "lat"]].copy()
out["rs_yield_tha"] = np.round(vals, 3)
out["rs_n_px"] = npx
out.to_csv(os.path.join(INT, "w25_r2_national_rs_target.csv"), index=False)
ok = ~out.rs_yield_tha.isna()
print(f"valid RS cells: {ok.sum()}/{len(out)} | mean {out.rs_yield_tha[ok].mean():.2f} +- {out.rs_yield_tha[ok].std():.2f} t/ha")
print("R2 done")
