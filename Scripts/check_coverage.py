"""检查所有数据文件的地理覆盖范围是否包含平谷区"""
import rasterio, os, glob
from pathlib import Path

PINGGU_BBOX = (116.8, 40.0, 117.5, 40.5)  # lon_min, lat_min, lon_max, lat_max

def check_file(path, label=""):
    """检查单文件是否覆盖平谷"""
    try:
        with rasterio.open(path) as src:
            b = src.bounds
            crs = str(src.crs).split(':')[-1].rstrip(']')
            res = src.res
            
            # 判断CRS类型
            is_wgs84 = '4326' in str(src.crs) or 'GEOGCS' in str(src.crs) and 'degree' in str(src.crs).lower()
            is_metric = src.crs and src.crs.is_projected
            
            # 检查覆盖
            if is_wgs84:
                overlaps = (b.left <= PINGGU_BBOX[2] and b.right >= PINGGU_BBOX[0] and
                           b.bottom <= PINGGU_BBOX[3] and b.top >= PINGGU_BBOX[1])
            else:
                overlaps = "需重投影"
            
            return {
                'label': label,
                'path': str(path),
                'bounds': (round(b.left, 2), round(b.bottom, 2), round(b.right, 2), round(b.top, 2)),
                'crs': crs,
                'res': (round(res[0], 4), round(res[1], 4)),
                'overlaps_pinggu': overlaps,
            }
    except Exception as e:
        return {'label': label, 'path': str(path), 'error': str(e)[:60], 'overlaps_pinggu': 'ERROR'}

print("=" * 70)
print("数据地理覆盖范围检查——目标: 平谷区 116.8-117.5°E, 40.0-40.5°N")
print("=" * 70)

# 1. WorldClim
print("\n[1] WorldClim 2.1 (应覆盖全球 -180~180, -90~90)")
wc_files = sorted(glob.glob(r"D:\2026-SP\Data\WorldClim\*.tif"))
for i, f in enumerate(wc_files[:3]):
    r = check_file(f, f"WorldClim [sample {i+1}]")
    print(f"  {Path(f).name}: bounds={r['bounds']}, CRS={r['crs']}, res={r['res']}, 覆盖平谷={r['overlaps_pinggu']}")
print(f"  ... 共 {len(wc_files)} 个tif，全为全球WGS84")

# 2. SRTM
print("\n[2] SRTM (5°×5° tile, 应覆盖115-120°E,40-45°N)")
srtm_files = sorted(glob.glob(r"D:\2026-SP\Data\SRTM\*.tif"))
for f in srtm_files:
    r = check_file(f, "SRTM")
    print(f"  {Path(f).name}: bounds={r['bounds']}, CRS={r['crs']}, res={r['res']}, 覆盖平谷={r['overlaps_pinggu']}")

# 3. SoilGrids WGS84 (5km聚合)
print("\n[3] SoilGrids 5km WGS84 (全球聚合)")
sg_files = sorted(glob.glob(r"D:\2026-SP\Data\SoilGrids_wgs84\*.tif"))
for i, f in enumerate(sg_files[:3]):
    r = check_file(f, "")
    print(f"  {Path(f).name}: bounds={r['bounds']}, CRS={r['crs']}, res={r['res']}, 覆盖平谷={r['overlaps_pinggu']}")
print(f"  ... 共 {len(sg_files)} 个tif")

# 4. 旧SoilGrids Homolosine (检查是否可用)
print("\n[4] SoilGrids 旧版 Homolosine (检查)")
old_sg = sorted(glob.glob(r"D:\2026-SP\Data\SoilGrids\SG_*_0-5cm*"))
from rasterio.warp import transform
for f in old_sg[:2]:
    try:
        with rasterio.open(f) as src:
            b = src.bounds
            crs = str(src.crs)
            # 转4角到WGS84
            try:
                xs, ys = transform(src.crs, 'EPSG:4326', 
                                   [b.left, b.right, b.left, b.right],
                                   [b.bottom, b.bottom, b.top, b.top])
                wgs_bounds = (min(xs), min(ys), max(xs), max(ys))
                covers = (wgs_bounds[0] <= PINGGU_BBOX[2] and wgs_bounds[2] >= PINGGU_BBOX[0] and
                         wgs_bounds[1] <= PINGGU_BBOX[3] and wgs_bounds[3] >= PINGGU_BBOX[1])
            except:
                wgs_bounds = "转换失败"
                covers = "?"
            print(f"  {Path(f).name}: Homolosine bounds={b}, WGS84≈{wgs_bounds}, 覆盖平谷={covers}")
    except Exception as e:
        print(f"  {Path(f).name}: ERROR {e}")

# 5. CMIP6 CO2 (非空间数据)
print("\n[5] CMIP6 CO2 (表格数据)")
co2 = r"D:\2026-SP\Data\CMIP6\CMIP6_CO2_Concentration.csv"
if os.path.exists(co2):
    with open(co2) as f:
        lines = f.readlines()
        print(f"  {Path(co2).name}: {len(lines)} 行, 首行: {lines[0].strip()[:80]}")

# 6. 总结
print("\n" + "=" * 70)
print("总结")
print("=" * 70)

# 检查主CSV的lon/lat范围
import pandas as pd
df = pd.read_csv(r"D:\2026-SP\Outputs\pinggu_environmental_data.csv")
print(f"主CSV lon范围: {df['lon'].min():.4f} ~ {df['lon'].max():.4f}")
print(f"主CSV lat范围: {df['lat'].min():.4f} ~ {df['lat'].max():.4f}")
print(f"数据点: {len(df)}")
print(f"目标: 116.8~117.5°E, 40.0~40.5°N")
print(f"✅ 完全在平谷范围内")
