"""下载 SoilGrids 5km WGS84 中国区域数据"""
import urllib.request, os, rasterio
from pathlib import Path

OUT = Path(r"D:\2026-SP\Data\SoilGrids_wgs84")
OUT.mkdir(exist_ok=True)

BASE = 'https://files.isric.org/soilgrids/latest/data_aggregated/5000m'
PROPS = {
    'clay': 'clay_pct',
    'sand': 'sand_pct', 
    'silt': 'silt_pct',
    'soc': 'soc_dgkg',
    'bdod': 'bdod_kgdm3',
    'cec': 'cec_cmolkg',
    'phh2o': 'ph',
    'nitrogen': 'nitrogen_cgkg',
}
DEPTH = '0-5cm'
STAT = 'mean'

total = len(PROPS)
for i, (prop, varname) in enumerate(PROPS.items()):
    fname = f'{prop}_{DEPTH}_{STAT}_5000.tif'
    out_path = OUT / fname
    url = f'{BASE}/{prop}/{fname}'
    
    if out_path.exists() and out_path.stat().st_size > 1000:
        print(f'[{i+1}/{total}] {prop}: 已存在 ({out_path.stat().st_size/1024/1024:.1f} MB)')
        continue
    
    print(f'[{i+1}/{total}] {prop}: 下载中...', end=' ', flush=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlretrieve(url, str(out_path))
        sz = out_path.stat().st_size / 1024 / 1024
        print(f'{sz:.1f} MB')
        
        # 验证
        with rasterio.open(out_path) as s:
            print(f'       CRS={s.crs}, Shape={s.shape}, Res={s.res}')
    except Exception as e:
        print(f'失败: {e}')

print('\n✅ 下载完成!')
print(f'目录: {OUT}')
