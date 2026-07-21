"""
从SoilGrids 5km WGS84-Homolosine提取平谷区数据并重投到WorldClim网格
"""
import rasterio, numpy as np, pandas as pd
from rasterio.warp import transform, Resampling
from rasterio.vrt import WarpedVRT
from pathlib import Path

SG_DIR = Path(r"D:\2026-SP\Data\SoilGrids_wgs84")
WC_CSV = Path(r"D:\2026-SP\Outputs\pinggu_environmental_data.csv")
OUT_CSV = Path(r"D:\2026-SP\Outputs\pinggu_environmental_data.csv")

# 读取已有WorldClim网格坐标
df = pd.read_csv(WC_CSV)
lons = df['lon'].values
lats = df['lat'].values
n = len(df)

# 目标CRS和transform (WorldClim WGS84)
with rasterio.open(r"D:\2026-SP\Data\WorldClim\wc2.1_2.5m_bio_1.tif") as ref:
    dst_crs = ref.crs
    dst_res = ref.res
    # 计算平谷区bounds
    bounds = (lons.min() - dst_res[0]/2, lats.min() - abs(dst_res[1])/2,
              lons.max() + dst_res[0]/2, lats.max() + abs(dst_res[1])/2)
    # 目标transform
    dst_width = 18
    dst_height = 13
    dst_transform = rasterio.transform.from_bounds(*bounds, dst_width, dst_height)

props = {
    'clay_0-5cm_mean_5000.tif': 'clay_pct',
    'sand_0-5cm_mean_5000.tif': 'sand_pct',
    'silt_0-5cm_mean_5000.tif': 'silt_pct',
    'soc_0-5cm_mean_5000.tif': 'soc_dgkg',
    'bdod_0-5cm_mean_5000.tif': 'bdod_kgdm3',
    'cec_0-5cm_mean_5000.tif': 'cec_cmolkg',
    'phh2o_0-5cm_mean_5000.tif': 'ph',
    'nitrogen_0-5cm_mean_5000.tif': 'nitrogen_cgkg',
}

print("重投影SoilGrids到WorldClim网格...")
for fname, varname in props.items():
    path = SG_DIR / fname
    if not path.exists():
        print(f"  {varname}: 文件不存在")
        continue
    
    try:
        with rasterio.open(path) as src:
            # 将目标bounds从WGS84转到源CRS
            src_bounds = transform('EPSG:4326', src.crs, 
                                   [bounds[0], bounds[2]], 
                                   [bounds[1], bounds[3]])
            
            with WarpedVRT(src, crs=dst_crs,
                          resampling=Resampling.average,
                          transform=dst_transform,
                          width=dst_width, height=dst_height) as vrt:
                data = vrt.read(1).astype(np.float32)
                nodata = vrt.nodatavals[0] if vrt.nodatavals else None
                if nodata is not None:
                    data[data == nodata] = np.nan
        
        df[varname] = data.flatten()
        valid = (~np.isnan(data)).sum()
        mean_val = np.nanmean(data)
        print(f"  {varname}: {valid}/{n} valid, mean={mean_val:.2f}")
    except Exception as e:
        print(f"  {varname}: 失败 - {e}")
        df[varname] = np.nan

# 保存
col_order = ['lon', 'lat'] + [c for c in df.columns if c not in ['lon', 'lat']]
df = df[col_order]
df.to_csv(OUT_CSV, index=False, float_format='%.4f')
print(f"\n✅ 土壤数据已并入: {OUT_CSV}")
print(f"   总变量: {len(df.columns)}")
