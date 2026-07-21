"""
平谷区环境数据全量提取脚本
WorldClim 19 bioclim + 12月prec + 12月tavg + bio5/6/13极端代理
+ SRTM elevation + slope/aspect + SoilGrids
输出: 统一CSV, 每行一个网格点
"""
import rasterio
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(r"D:\2026-SP\Data")
OUT = Path(r"D:\2026-SP\Outputs")
OUT.mkdir(exist_ok=True)

# ==== Pinggu bbox ====
LON_MIN, LON_MAX = 116.8, 117.5
LAT_MIN, LAT_MAX = 40.0, 40.5

def extract_grid(rasters, lon_min, lon_max, lat_min, lat_max, variable_names):
    """
    从多个raster中提取统一网格的值
    rasters: list of (filepath, band_index) or filepath
    返回 DataFrame with columns: lon, lat, var1, var2, ...
    """
    # 用第一个raster确定网格
    r0 = rasters[0] if isinstance(rasters[0], tuple) else (rasters[0], 1)
    if isinstance(r0, tuple):
        r0_path = r0[0]
    else:
        r0_path = r0
    
    with rasterio.open(r0_path) as src:
        # 窗口读取
        row_start, col_start = src.index(lon_min, lat_max)
        row_end, col_end = src.index(lon_max, lat_min)
        row_start, row_end = min(row_start, row_end), max(row_start, row_end)
        col_start, col_end = min(col_start, col_end), max(col_start, col_end)
        
        window = rasterio.windows.Window(col_start, row_start, 
                                          col_end - col_start + 1, 
                                          row_end - row_start + 1)
        transform = src.window_transform(window)
        
        nrows = row_end - row_start + 1
        ncols = col_end - col_start + 1
        
        # 生成坐标数组
        lons = np.zeros((nrows, ncols))
        lats = np.zeros((nrows, ncols))
        for r in range(nrows):
            for c in range(ncols):
                lon, lat = rasterio.transform.xy(transform, r, c)
                lons[r, c] = lon
                lats[r, c] = lat
    
    values = np.zeros((nrows, ncols, len(rasters)))
    
    for i, rast in enumerate(rasters):
        if isinstance(rast, tuple):
            path, band = rast
        else:
            path, band = rast, 1
        
        with rasterio.open(path) as src:
            data = src.read(band, window=window, masked=True)
            if data.ndim == 3:
                data = data[0]
            # 转为float处理nodata
            if np.issubdtype(data.dtype, np.integer):
                data = data.astype(np.float32)
                nodata = src.nodatavals[band-1] if src.nodatavals else None
                if nodata is not None:
                    data[data == nodata] = np.nan
        
        if np.issubdtype(data.dtype, np.integer):
            data = data.astype(np.float32)
        values[:, :, i] = data.filled(np.nan) if hasattr(data, 'filled') else data
    
    # 展平为DataFrame
    records = []
    for r in range(nrows):
        for c in range(ncols):
            if np.all(np.isnan(values[r, c, :])):
                continue
            rec = {'lon': round(lons[r, c], 6), 'lat': round(lats[r, c], 6)}
            for j, name in enumerate(variable_names):
                rec[name] = round(float(values[r, c, j]), 4)
            records.append(rec)
    
    return pd.DataFrame(records)


print("=" * 60)
print("平谷区环境数据全量提取")
print(f"区域: {LON_MIN}-{LON_MAX}E, {LAT_MIN}-{LAT_MAX}N")
print("=" * 60)

# ===== 1. WorldClim Bioclimatic (bio1-bio19) + 极端代理 =====
print("\n[1/5] 提取 WorldClim Bioclimatic 变量...")
bio_names = [f'bio{i}' for i in range(1, 20)]
bio_paths = [str(BASE / 'WorldClim' / f'wc2.1_2.5m_bio_{i}.tif') for i in range(1, 20)]
df_bio = extract_grid(bio_paths, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, bio_names)
print(f"  {len(df_bio)} 个网格点, {len(bio_names)} 个变量")

# 添加极端气候代理标记
df_bio['extreme_Tmax_proxy'] = df_bio['bio5']  # bio5 = Max Temperature of Warmest Month
df_bio['extreme_Tmin_proxy'] = df_bio['bio6']  # bio6 = Min Temperature of Coldest Month  
df_bio['extreme_Prec_proxy'] = df_bio['bio13'] # bio13 = Precipitation of Wettest Month

print(f"  极端代理: bio5(Tmax)={df_bio['bio5'].mean():.1f}°C, bio6(Tmin)={df_bio['bio6'].mean():.1f}°C, bio13(Prec)={df_bio['bio13'].mean():.0f}mm")

# ===== 2. WorldClim Monthly =====
print("\n[2/5] 提取 WorldClim 月度数据...")
monthly_names = []
monthly_paths = []

for m in range(1, 13):
    monthly_names.append(f'prec_{m:02d}')
    monthly_paths.append(str(BASE / 'WorldClim' / f'wc2.1_2.5m_prec_{m:02d}.tif'))

for m in range(1, 13):
    monthly_names.append(f'tavg_{m:02d}')
    monthly_paths.append(str(BASE / 'WorldClim' / f'wc2.1_2.5m_tavg_{m:02d}.tif'))

df_monthly = extract_grid(monthly_paths, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, monthly_names)

# 计算 GDD (Growing Degree Days, base 10°C)
for m in range(1, 13):
    t = df_monthly[f'tavg_{m:02d}']
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gdd = np.maximum(t - 10, 0) * days_in_month[m-1]
    df_monthly[f'GDD_{m:02d}'] = gdd

# 生长季 GDD (3-9月) + 全年 GDD
gdd_cols = [f'GDD_{m:02d}' for m in range(3, 10)]
df_monthly['GDD_gs'] = df_monthly[gdd_cols].sum(axis=1)
df_monthly['GDD_annual'] = df_monthly[[f'GDD_{m:02d}' for m in range(1, 13)]].sum(axis=1)

print(f"  {len(df_monthly)} 网格点, 24个月度变量 + 8个GDD")
print(f"  GDD_gs(生长季)={df_monthly['GDD_gs'].mean():.0f}, GDD_annual={df_monthly['GDD_annual'].mean():.0f}")

# ===== 3. SRTM Elevation + 派生 =====
print("\n[3/5] 提取 SRTM 海拔...")
srtm_path = str(BASE / 'SRTM' / 'srtm_60_04.tif')
df_elev = extract_grid([(srtm_path, 1)], LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, ['elevation_m'])
print(f"  elevation range: {df_elev['elevation_m'].min():.0f} - {df_elev['elevation_m'].max():.0f} m")

# 计算 slope 和 aspect (用numpy梯度)
from rasterio.windows import Window
with rasterio.open(srtm_path) as src:
    row_s, col_s = src.index(LON_MIN, LAT_MAX)
    row_e, col_e = src.index(LON_MAX, LAT_MIN)
    row_s, row_e = min(row_s, row_e), max(row_s, row_e)
    col_s, col_e = min(col_s, col_e), max(col_s, col_e)
    elev_data = src.read(1, window=Window(col_s, row_s, col_e-col_s+1, row_e-row_s+1))
    res = src.res[0]

gy, gx = np.gradient(elev_data, res)
slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
slope_deg = np.degrees(slope_rad)
aspect_rad = np.arctan2(-gx, gy)  # standard: 0=N, clockwise
aspect_deg = np.degrees(aspect_rad)
aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360, aspect_deg)

slopes = slope_deg.flatten()
aspects = aspect_deg.flatten()
mask = ~np.isnan(elev_data.flatten())
slopes = np.where(mask, slopes, np.nan)
aspects = np.where(mask, aspects, np.nan)

df_elev['slope_deg'] = [round(s, 2) if not np.isnan(s) else np.nan for s in slopes]
df_elev['aspect_deg'] = [round(a, 2) if not np.isnan(a) else np.nan for a in aspects]
print(f"  slope: {np.nanmean(slopes):.1f}° mean, aspect: {np.nanmean(aspects):.0f}° mean")

# ===== 4. SoilGrids =====
print("\n[4/5] 提取 SoilGrids 数据...")
soil_dir = BASE / 'SoilGrids'
soil_rasters = [
    (str(soil_dir / 'clay_0-5cm_mean.vrt'), 1),
    (str(soil_dir / 'sand_0-5cm_mean.vrt'), 1),
    (str(soil_dir / 'silt_0-5cm_mean.vrt'), 1),
    (str(soil_dir / 'nitrogen_0-5cm_mean.vrt'), 1),
    (str(soil_dir / 'soc_0-5cm_mean.vrt'), 1),
]
soil_names = ['clay_pct', 'sand_pct', 'silt_pct', 'nitrogen_cgkg', 'soc_dgkg']
df_soil = extract_grid(soil_rasters, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX, soil_names)

print(f"  clay: {df_soil['clay_pct'].mean():.0f}%, sand: {df_soil['sand_pct'].mean():.0f}%")
print(f"  nitrogen: {df_soil['nitrogen_cgkg'].mean():.0f} cg/kg, SOC: {df_soil['soc_dgkg'].mean():.0f} dg/kg")

# ===== 5. 合并 =====
print("\n[5/5] 合并所有变量...")

# Merge on lon/lat (round to avoid floating issues)
def merge_dfs(dfs):
    result = dfs[0].copy()
    for d in dfs[1:]:
        result = pd.merge(result, d, on=['lon', 'lat'], how='inner')
    return result

df_all = merge_dfs([df_bio, df_monthly, df_elev, df_soil])

# 列排序：坐标 + 极端代理 + bioclim + 月度 + GDD + 地形 + 土壤
extreme_cols = ['extreme_Tmax_proxy', 'extreme_Tmin_proxy', 'extreme_Prec_proxy']
bio_cols = [c for c in df_all.columns if c.startswith('bio')]
monthly_prec = [c for c in df_all.columns if c.startswith('prec_')]
monthly_tavg = [c for c in df_all.columns if c.startswith('tavg_')]
gdd_cols_all = [c for c in df_all.columns if c.startswith('GDD_')]
terrain_cols = ['elevation_m', 'slope_deg', 'aspect_deg']
soil_all = ['clay_pct', 'sand_pct', 'silt_pct', 'nitrogen_cgkg', 'soc_dgkg']

col_order = ['lon', 'lat'] + extreme_cols + bio_cols + monthly_prec + monthly_tavg + gdd_cols_all + terrain_cols + soil_all
df_all = df_all[col_order]

# 保存
output_csv = OUT / 'pinggu_environmental_data.csv'
df_all.to_csv(output_csv, index=False, float_format='%.4f')

# ===== 摘要 =====
n_cols = len(df_all.columns)
n_rows = len(df_all)
print(f"\n{'='*60}")
print(f"✅ 提取完成!")
print(f"   网格数: {n_rows}")
print(f"   变量数: {n_cols}")
print(f"   输出: {output_csv}")
print(f"\n变量清单:")
print(f"   坐标: lon, lat")
print(f"   极端代理: bio5(Tmax_95p), bio6(Tmin_5p), bio13(Prec_95p)")
print(f"   Bioclim: bio1-bio19 (19个)")
print(f"   月度降水: prec_01-12 (12个)")
print(f"   月均温: tavg_01-12 (12个)")
print(f"   GDD: GDD_01-12 + GDD_gs + GDD_annual (14个)")
print(f"   地形: elevation, slope, aspect (3个)")
print(f"   土壤: clay, sand, silt, N, SOC (5个)")
print(f"   总计: {n_cols}列")
print(f"\n缺失数据说明:")
print(f"   - SoilGrids 补充3属性(phh2o/bdod/cec)待手动下载")
print(f"   - 中国土壤数据(SAT/DUL/LL15)待获取")
print(f"   - CHELSA逐日极端指数 → 已用bio5/6/13代理")
print(f"   - 品种性状模板待填入")
