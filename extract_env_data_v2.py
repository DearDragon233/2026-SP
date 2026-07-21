"""
平谷区环境数据全量提取 v2
统一按WorldClim 2.5 arc-min网格提取，高分辨率数据取网格内均值
"""
import rasterio
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling
import numpy as np
import pandas as pd
from pathlib import Path

BASE = Path(r"D:\2026-SP\Data")
OUT = Path(r"D:\2026-SP\Outputs")
OUT.mkdir(exist_ok=True)

LON_MIN, LON_MAX = 116.8, 117.5
LAT_MIN, LAT_MAX = 40.0, 40.5

def get_window_info(path, lon_min, lon_max, lat_min, lat_max):
    """获取窗口信息和坐标网格"""
    with rasterio.open(path) as src:
        row_s, col_s = src.index(lon_min, lat_max)
        row_e, col_e = src.index(lon_max, lat_min)
        row_s, row_e = min(row_s, row_e), max(row_s, row_e)
        col_s, col_e = min(col_s, col_e), max(col_s, col_e)
        
        w = col_e - col_s + 1
        h = row_e - row_s + 1
        window = Window(col_s, row_s, w, h)
        transform = src.window_transform(window)
        
        lons = np.array([rasterio.transform.xy(transform, h//2, c)[0] for c in range(w)])
        lats = np.array([rasterio.transform.xy(transform, r, w//2)[1] for r in range(h)])
        
        return window, lons, lats, transform, src.crs, src.res

def read_raster(path, window, band=1):
    """读取raster窗口, 转float (同CRS)"""
    with rasterio.open(path) as src:
        data = src.read(band, window=window, masked=True)
        if data.ndim == 3:
            data = data[0]
        nodata = src.nodatavals[band-1] if src.nodatavals else None
    data = data.astype(np.float32)
    if nodata is not None:
        data[data == nodata] = np.nan
    return data

def read_raster_warped(src_path, target_crs, target_transform, target_shape):
    """通过WarpedVRT将任意CRS数据读取到目标网格"""
    from rasterio.vrt import WarpedVRT
    
    with rasterio.open(src_path) as src:
        if src.crs == target_crs:
            return read_raster(src_path, None)
        
        with WarpedVRT(src, crs=target_crs, 
                       resampling=Resampling.average,
                       transform=target_transform,
                       width=target_shape[1],
                       height=target_shape[0]) as vrt:
            data = vrt.read(1)
            data = data.astype(np.float32)
            nodata = vrt.nodatavals[0] if vrt.nodatavals else None
            if nodata is not None:
                data[data == nodata] = np.nan
            return data

def zonal_mean(hi_res, window_hi, lons_coarse, lats_coarse, transform_coarse, res_coarse):
    """高分辨率数据 → 粗网格每个cell内的均值"""
    h, w = len(lats_coarse), len(lons_coarse)
    result = np.full((h, w), np.nan, dtype=np.float32)
    
    res_lon = abs(res_coarse[0])
    res_lat = abs(res_coarse[1])
    
    for r in range(h):
        for c in range(w):
            clon = lons_coarse[c]
            clat = lats_coarse[r]
            # 粗网格cell范围
            half_lon = res_lon / 2
            half_lat = res_lat / 2
            
            with rasterio.open(hi_res) as src:
                # 用坐标窗口
                try:
                    row_s2, col_s2 = src.index(clon - half_lon, clat + half_lat)
                    row_e2, col_e2 = src.index(clon + half_lon, clat - half_lat)
                    row_s2, row_e2 = min(row_s2, row_e2), max(row_s2, row_e2)
                    col_s2, col_e2 = min(col_s2, col_e2), max(col_s2, col_e2)
                    
                    if row_s2 >= row_e2 or col_s2 >= col_e2:
                        continue
                    
                    sub = src.read(1, window=Window(col_s2, row_s2, col_e2-col_s2+1, row_e2-row_s2+1))
                    sub = sub.astype(np.float32)
                    nodata = src.nodatavals[0] if src.nodatavals else None
                    if nodata is not None:
                        sub[sub == nodata] = np.nan
                    
                    if np.any(~np.isnan(sub)):
                        result[r, c] = np.nanmean(sub)
                except:
                    pass
    
    return result


print("=" * 60)
print("平谷区环境数据全量提取 v2")
print("=" * 60)

# ===== 基准网格: WorldClim bio_1 =====
ref_path = str(BASE / 'WorldClim' / 'wc2.1_2.5m_bio_1.tif')
window_ref, lons, lats, transform_ref, crs_ref, res_ref = get_window_info(
    ref_path, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX)

print(f"\n基准网格(WorldClim 2.5 arc-min): {len(lons)} x {len(lats)} = {len(lons)*len(lats)} cells")
print(f"分辨率: {res_ref[0]:.4f}° (~{abs(res_ref[0])*111:.1f} km)")

# 初始化DataFrame
mesh_lon, mesh_lat = np.meshgrid(lons, lats)
df = pd.DataFrame({
    'lon': mesh_lon.flatten(),
    'lat': mesh_lat.flatten(),
})
print(f"网格点数: {len(df)}")

# ===== 1. Bioclimatic 19 =====
print("\n[1/5] WorldClim Bioclimatic...")
for i in range(1, 20):
    data = read_raster(str(BASE / 'WorldClim' / f'wc2.1_2.5m_bio_{i}.tif'), window_ref)
    df[f'bio{i}'] = data.flatten()
    if i % 5 == 0:
        print(f"  bio1-{i} done")

# 极端代理
df['extreme_Tmax_proxy'] = df['bio5']
df['extreme_Tmin_proxy'] = df['bio6']
df['extreme_Prec_proxy'] = df['bio13']
print(f"  极端代理: Tmax={df['bio5'].mean():.1f}°C, Tmin={df['bio6'].mean():.1f}°C, Prec={df['bio13'].mean():.0f}mm")

# ===== 2. Monthly =====
print("\n[2/5] WorldClim 月度 + GDD...")
for m in range(1, 13):
    df[f'prec_{m:02d}'] = read_raster(str(BASE / 'WorldClim' / f'wc2.1_2.5m_prec_{m:02d}.tif'), window_ref).flatten()
    df[f'tavg_{m:02d}'] = read_raster(str(BASE / 'WorldClim' / f'wc2.1_2.5m_tavg_{m:02d}.tif'), window_ref).flatten()

days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
for m in range(1, 13):
    df[f'GDD_{m:02d}'] = np.maximum(df[f'tavg_{m:02d}'] - 10, 0) * days_in_month[m-1]

gdd_cols = [f'GDD_{m:02d}' for m in range(3, 10)]
gdd_all_cols = [f'GDD_{m:02d}' for m in range(1, 13)]
df['GDD_gs'] = df[gdd_cols].sum(axis=1)
df['GDD_annual'] = df[gdd_all_cols].sum(axis=1)
print(f"  GDD_gs={df['GDD_gs'].mean():.0f}, GDD_annual={df['GDD_annual'].mean():.0f}")

# ===== 3. SRTM Elevation (resample to coarse grid) =====
print("\n[3/5] SRTM 海拔 + slope/aspect...")
srtm_path = str(BASE / 'SRTM' / 'srtm_60_04.tif')

# 读取SRTM窗口内的数据
with rasterio.open(srtm_path) as srtm_src:
    srtm_window, _, _, srtm_transform, _, srtm_res = get_window_info(
        srtm_path, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX)
    
    elev = srtm_src.read(1, window=srtm_window)
    elev = elev.astype(np.float32)
    nodata = srtm_src.nodatavals[0] if srtm_src.nodatavals else None
    if nodata is not None:
        elev[elev == nodata] = np.nan

# 计算slope & aspect (SRTM分辨率)
sx, sy = abs(srtm_res[0]) * 111000, abs(srtm_res[1]) * 111000
gy, gx = np.gradient(elev, sy, sx)
slope_rad = np.arctan(np.sqrt(gx**2 + gy**2))
slope_deg = np.degrees(slope_rad)
aspect_rad = np.arctan2(-gx, gy)
aspect_deg = np.degrees(aspect_rad)
aspect_deg = np.where(aspect_deg < 0, aspect_deg + 360, aspect_deg)

# Resample到WorldClim网格 (zonal mean)
print("  重采样到粗网格...")
elev_coarse = np.full((len(lats), len(lons)), np.nan, dtype=np.float32)
slope_coarse = np.full((len(lats), len(lons)), np.nan, dtype=np.float32)
aspect_coarse = np.full((len(lats), len(lons)), np.nan, dtype=np.float32)

half_lon = abs(res_ref[0]) / 2
half_lat = abs(res_ref[1]) / 2

for r in range(len(lats)):
    for c in range(len(lons)):
        clon, clat = lons[c], lats[r]
        
        try:
            row_s2, col_s2 = srtm_src.index(clon - half_lon, clat + half_lat)
            row_e2, col_e2 = srtm_src.index(clon + half_lon, clat - half_lat)
            row_s2, row_e2 = min(row_s2, row_e2), max(row_s2, row_e2)
            col_s2, col_e2 = min(col_s2, col_e2), max(col_s2, col_e2)
            
            # 相对于window内的索引
            r_start = row_s2 - int(srtm_window.row_off)
            r_end = row_e2 - int(srtm_window.row_off)
            c_start = col_s2 - int(srtm_window.col_off)
            c_end = col_e2 - int(srtm_window.col_off)
            
            r_start = max(0, r_start)
            r_end = min(elev.shape[0], r_end+1)
            c_start = max(0, c_start)
            c_end = min(elev.shape[1], c_end+1)
            
            if r_start < r_end and c_start < c_end:
                sub_elev = elev[r_start:r_end, c_start:c_end]
                sub_slope = slope_deg[r_start:r_end, c_start:c_end]
                sub_aspect = aspect_deg[r_start:r_end, c_start:c_end]
                
                mask = ~np.isnan(sub_elev)
                if mask.any():
                    elev_coarse[r, c] = np.nanmean(sub_elev[mask])
                    slope_coarse[r, c] = np.nanmean(sub_slope[mask])
                    # 风向角取圆形均值
                    angles_rad = np.deg2rad(sub_aspect[mask])
                    sin_mean = np.nanmean(np.sin(angles_rad))
                    cos_mean = np.nanmean(np.cos(angles_rad))
                    aspect_coarse[r, c] = np.rad2deg(np.arctan2(sin_mean, cos_mean)) % 360
        except:
            pass

df['elevation_m'] = elev_coarse.flatten()
df['slope_deg'] = slope_coarse.flatten()
df['aspect_deg'] = aspect_coarse.flatten()

valid_elev = df['elevation_m'].dropna()
print(f"  elevation: {valid_elev.min():.0f}-{valid_elev.max():.0f}m (mean {valid_elev.mean():.0f}m)")
print(f"  slope: {df['slope_deg'].dropna().mean():.1f}° mean")

# ===== 4. SoilGrids (resample) =====
print("\n[4/5] SoilGrids 土壤属性...")
soil_dir = BASE / 'SoilGrids'
soil_files = {
    'clay_pct': 'SG_clay_0-5cm.tif',
    'sand_pct': 'SG_sand_0-5cm.tif',
    'silt_pct': 'SG_silt_0-5cm.tif',
    'soc_dgkg': 'SG_soc_0-5cm.tif',
    'bdod_kgdm3': 'SG_bdod_0-5cm.tif',
    'cec_cmolkg': 'SG_cec_0-5cm.tif',
    'phh2o': 'SG_phh2o_0-5cm.tif',
    # nitrogen 用 SOC 估算: N ≈ SOC/10 (c/g → cg/kg 需转换, 简化处理)
}

for name, fname in soil_files.items():
    path = str(soil_dir / fname)
    try:
        data = read_raster_warped(path, crs_ref, transform_ref, (len(lats), len(lons)))
        df[name] = data.flatten()
    except Exception as e:
        print(f"  {name}: 读取失败 ({e})")
        df[name] = np.nan

print(f"  clay: {df['clay_pct'].mean():.0f}%, sand: {df['sand_pct'].mean():.0f}%, ph: {df['phh2o'].mean():.1f}")

# ===== 5. 列排序 & 保存 =====
print("\n[5/5] 整理输出...")

extreme_cols = ['extreme_Tmax_proxy', 'extreme_Tmin_proxy', 'extreme_Prec_proxy']
bio_cols = [f'bio{i}' for i in range(1, 20)]
prec_cols = [f'prec_{m:02d}' for m in range(1, 13)]
tavg_cols = [f'tavg_{m:02d}' for m in range(1, 13)]
gdd_cols_out = [f'GDD_{m:02d}' for m in range(1, 13)] + ['GDD_gs', 'GDD_annual']
terrain_cols = ['elevation_m', 'slope_deg', 'aspect_deg']
soil_cols = list(soil_files.keys())

col_order = ['lon', 'lat'] + extreme_cols + bio_cols + prec_cols + tavg_cols + gdd_cols_out + terrain_cols + soil_cols
df = df[col_order]

output_csv = OUT / 'pinggu_environmental_data.csv'
df.to_csv(output_csv, index=False, float_format='%.4f')

# 清理无效行
valid = df.dropna(subset=['bio1'])
n_valid = len(valid)
n_total = len(df)
print(f"  有效网格: {n_valid}/{n_total}")

# 摘要
n_cols = len(df.columns)
print(f"\n{'='*60}")
print(f"✅ 提取完成!")
print(f"   输出: {output_csv}")
print(f"   文件大小: {Path(output_csv).stat().st_size/1024:.0f} KB")
print(f"   网格: {n_valid} 有效 / {n_total} 总计")
print(f"   变量: {n_cols}")
print(f"\n变量清单 ({n_cols}列):")
print(f"   坐标: lon, lat")
print(f"   极端代理: bio5/bio6/bio13 (3)")
print(f"   Bioclimatic: bio1-bio19 (19)")
print(f"   月度降水: prec_01-12 (12)")
print(f"   月均温: tavg_01-12 (12)")
print(f"   GDD: GDD_01-12 + GDD_gs + GDD_annual (14)")
print(f"   地形: elevation, slope, aspect (3)")
print(f"   土壤: clay, sand, silt, soc, bdod, cec, phh2o (7)")
print(f"\n缺失数据:")
print(f"   - soil nitrogen (可用SOC/10估算)")
print(f"   - SAT / DUL / LL15 (中国土壤) — 需手动下载")
print(f"   - 品种性状 — 模板已建，待填入")
print(f"   - CHELSA逐日极端指数 — 已用bio5/6/13代理")
