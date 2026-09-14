
import rasterio, numpy as np, pandas as pd, os
from rasterio.windows import Window
from rasterio.warp import transform as warp_transform
from pyproj import Transformer

ROOT = r"D:\2026-SP"
# 读产量 301 点坐标
df_y = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_yield.csv"))
centers = df_y[["lon", "lat"]].values
print("centers:", len(centers), "| lon range:", centers[:,0].min().round(3), "-", centers[:,0].max().round(3),
      "| lat:", centers[:,1].min().round(3), "-", centers[:,1].max().round(3))

def extract_robust(tif_path, name):
    with rasterio.open(tif_path) as src:
        nod = src.nodata
        vals = []
        # 如果 CRS 不是 4326，先转换中心点坐标
        if src.crs and src.crs.to_epsg() != 4326:
            tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            xs, ys = tr.transform(centers[:,0], centers[:,1])
        else:
            xs, ys = centers[:,0], centers[:,1]
        for x, y in zip(xs, ys):
            try:
                r, c = rasterio.transform.rowcol(src.transform, x, y)
                r = max(0, min(r, src.height-1)); c = max(0, min(c, src.width-1))
                v = src.read(1, window=Window(c, r, 1, 1))[0,0]
                v = float(v)
                if nod is not None and abs(v - nod) < abs(nod)*0.01: v = np.nan
                if v < -1e10: v = np.nan
                vals.append(v)
            except Exception as e:
                vals.append(np.nan)
    s = pd.Series(vals).dropna()
    print(f"  {name}: {len(s)}/{len(vals)} valid, mean={s.mean():.2f}" if len(s) else f"  {name}: 0 valid")
    return vals

feats = {}
feats["elevation_m"] = extract_robust(os.path.join(ROOT, "Data", "SRTM", "srtm_60_04.tif"), "elevation_m")
for f in os.listdir(os.path.join(ROOT, "Data", "SoilGrids_wgs84")):
    if f.endswith(".tif"):
        nm = f.replace(".tif","").split("_0-5")[0]
        feats[nm] = extract_robust(os.path.join(ROOT, "Data", "SoilGrids_wgs84", f), nm)
for f in ["wc2.1_2.5m_bio_1.tif", "wc2.1_2.5m_bio_4.tif", "wc2.1_2.5m_bio_5.tif",
          "wc2.1_2.5m_bio_12.tif", "wc2.1_2.5m_bio_15.tif", "wc2.1_2.5m_bio_10.tif"]:
    nm = f.replace("wc2.1_2.5m_", "").replace(".tif", "")
    feats[nm] = extract_robust(os.path.join(ROOT, "Data", "WorldClim", f), nm)

# 合并
df_f = pd.DataFrame({"lon": centers[:,0], "lat": centers[:,1], **feats})
out = df_y.merge(df_f, on=["lon","lat"], how="left")
out.to_csv(os.path.join(ROOT, "Outputs", "intermediate", "fine250_merged_fixed.csv"), index=False)
print("\nsaved fine250_merged_fixed.csv | shape:", out.shape)
nv = out.select_dtypes("number").isna().sum()
print("NaN per col:"); print(nv[nv>0])
