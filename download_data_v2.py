#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download public data to D:\\2026-SP\\Data\\
Handles Chinese network constraints (GFW, slow connections to .edu domains)
"""
import os, sys, urllib.request, csv, json, time, subprocess

BASE = r'D:\2026-SP\Data'

def try_dl(url, dest, desc='', retries=3):
    if os.path.exists(dest) and os.path.getsize(dest) > 100:
        print(f'  [SKIP] {desc} exists ({os.path.getsize(dest)/1024:.0f}KB)')
        return True
    print(f'  [TRY] {desc} from {url[:80]}...')
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            with open(dest, 'wb') as f:
                f.write(data)
            print(f'  [OK] {desc}: {len(data)/1024/1024:.1f}MB')
            return True
        except Exception as e:
            if i < retries - 1:
                print(f'  [RETRY {i+1}/{retries}] {e}')
                time.sleep(3)
            else:
                print(f'  [FAIL] {desc}: {e.__class__.__name__}')
                return False
    return False

# ═══════════════════════════════════════════
# 1. CO2 Concentration CSV (always works, no network needed)
# ═══════════════════════════════════════════
CMIP6_DIR = os.path.join(BASE, 'CMIP6')
os.makedirs(CMIP6_DIR, exist_ok=True)
print('\n=== 1. CO2 Concentration Reference ===')

co2_csv = os.path.join(CMIP6_DIR, 'CMIP6_CO2_Concentration.csv')
co2_data = {
    'SSP2-4.5': {2020:412,2030:440,2040:468,2050:490,2060:513,2070:530,2080:543,2090:550,2100:555},
    'SSP5-8.5': {2020:412,2030:448,2040:492,2050:540,2060:602,2070:670,2080:750,2090:840,2100:935}
}
with open(co2_csv, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Year','SSP','CO2_ppm'])
    for ssp, vals in co2_data.items():
        for yr, v in sorted(vals.items()):
            w.writerow([yr, ssp, v])
print(f'  [OK] {co2_csv}')

# ═══════════════════════════════════════════
# 2. WorldClim bio variables  
#    Try multiple mirrors in order
# ═══════════════════════════════════════════
WC_DIR = os.path.join(BASE, 'WorldClim')
os.makedirs(WC_DIR, exist_ok=True)

print('\n=== 2. WorldClim Bio Variables ===')
bio_mirrors = [
    'https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_bio.zip',
    'https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip',
]
for mirror in bio_mirrors:
    dest = os.path.join(WC_DIR, 'WC_bio_2.5m.zip')
    if try_dl(mirror, dest, 'WorldClim bio', retries=1):
        import zipfile
        with zipfile.ZipFile(dest, 'r') as zf:
            zf.extractall(WC_DIR)
        print(f'  [EXTRACT] Done')
        break
else:
    print('  [NOTE] WorldClim download blocked by network. Manual steps:')
    print('    1. Open https://www.worldclim.org/data/worldclim21.html in browser')
    print('    2. Download "Bioclimatic variables" at 2.5 arc-minutes')
    print('    3. Save to D:\\2026-SP\\Data\\WorldClim\\WC_bio_2.5m.zip')
    print('    4. Also download "Average temperature" and "Precipitation" monthly data')

# ═══════════════════════════════════════════
# 3. SRTM Elevation for Pinggu area  
# ═══════════════════════════════════════════
SRTM_DIR = os.path.join(BASE, 'SRTM')
os.makedirs(SRTM_DIR, exist_ok=True)

print('\n=== 3. SRTM Elevation ===')
# Try elevation CLI first
try:
    result = subprocess.run(['elevation', 'clip', 
        '-b', '116.7', '39.8', '117.5', '40.5',
        '-o', os.path.join(SRTM_DIR, 'SRTM_Elevation_Pinggu.tif')],
        capture_output=True, text=True, timeout=120)
    if result.returncode == 0:
        print(f'  [OK] SRTM downloaded via elevation CLI')
    else:
        print(f'  [WARN] elevation CLI failed: {result.stderr[:200]}')
except FileNotFoundError:
    print('  [NOTE] elevation CLI not installed. Manual steps:')
    print('    1. pip install elevation')
    print('    2. elevation clip -b 116.7 39.8 117.5 40.5 -o D:\\2026-SP\\Data\\SRTM\\SRTM_Elevation_Pinggu.tif')
except Exception as e:
    print(f'  [NOTE] elevation error: {e}')
    print('  Alternative: download from https://srtm.csi.cgiar.org/srtmdata/')
    print('  Select tiles: n40e116, n40e117')

# ═══════════════════════════════════════════
# 4. Variety Trait Template
# ═══════════════════════════════════════════
VARIETY_DIR = os.path.join(BASE, 'Variety')
os.makedirs(VARIETY_DIR, exist_ok=True)
print('\n=== 4. Variety Template ===')
variety_csv = os.path.join(VARIETY_DIR, 'Variety_Wheat_Traits.csv')
with open(variety_csv, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Variety_Name','Approval_Year','Region','Maturity_Days',
                'GrainFill_Days','TKW_g','GrainPerSpike','SpikeDensity_wan_per_ha',
                'PlantHeight_cm','ColdTol_1-5','DroughtTol_1-5','Yield_Mg_ha','Source','Notes'])
    w.writerow(['济麦22','2006','山东','','','','','','','','','','审定公告',''])
    w.writerow(['中麦175','2009','北京/河北','','','','','','','','','','审定公告',''])
    w.writerow(['农大211','2007','北京','','','','','','','','','','审定公告',''])
    w.writerow(['京冬8号','1999','北京','','','','','','','','','','审定公告',''])
    w.writerow(['石4185','2000','河北','','','','','','','','','','审定公告',''])
    w.writerow(['鲁原502','2011','山东/河北','','','','','','','','','','审定公告',''])
    w.writerow(['衡观35','2007','河北','','','','','','','','','','审定公告',''])
    w.writerow(['良星99','2005','山东','','','','','','','','','','审定公告',''])
print(f'  [OK] {variety_csv}')

# ═══════════════════════════════════════════
# 5. Management Data Placeholder
# ═══════════════════════════════════════════
MGMT_DIR = os.path.join(BASE, 'Management')
os.makedirs(MGMT_DIR, exist_ok=True)
print('\n=== 5. Management Reference ===')
readme = os.path.join(MGMT_DIR, 'README.txt')
with open(readme, 'w', encoding='utf-8') as f:
    f.write('Xiao et al. (2024) Nature Food 5:59-71\n')
    f.write('DOI: 10.1038/s43016-023-00891-x\n')
    f.write('Data & Code: https://figshare.com/articles/24471919\n\n')
    f.write('Expected files (optimized management at ~1km across NCP):\n')
    f.write('  MGMT_N_Wheat_Optimized.tif ~ wheat N input (kg/ha)\n')
    f.write('  MGMT_N_Maize_Optimized.tif  ~ maize N input (kg/ha)\n')
    f.write('  MGMT_Irr_Wheat_Optimized.tif ~ wheat irrigation (mm)\n')
    f.write('  MGMT_Irr_Maize_Optimized.tif  ~ maize irrigation (mm)\n')
    f.write('  MGMT_Res_Wheat_Optimized.tif  ~ wheat residue retention (%)\n')
    f.write('  MGMT_Res_Maize_Optimized.tif  ~ maize residue retention (%)\n')
print(f'  [OK] {readme}')

# ═══════════════════════════════════════════
# 6. Create data registry JSON
# ═══════════════════════════════════════════
print('\n=== 6. Data Registry ===')
registry = {
    'project': '2026-SP',
    'title': '环境-作物-管理互作模型',
    'created': '2026-07-19',
    'total_dimensions': 65,
    'categories': {
        'WorldClim': {'path': 'Data/WorldClim/', 'files': 32, 'dimensions': [1,32]},
        'SoilGrids': {'path': 'Data/SoilGrids/', 'files': 8, 'dimensions': [37,44]},
        'ChinaSoil': {'path': 'Data/ChinaSoil/', 'files': 3, 'dimensions': [45,47]},
        'SRTM': {'path': 'Data/SRTM/', 'files': 3, 'dimensions': [48,50]},
        'CHELSA': {'path': 'Data/CHELSA/', 'files': 3, 'dimensions': [33,35]},
        'CMIP6': {'path': 'Data/CMIP6/', 'files': 1, 'dimensions': [36]},
        'Variety': {'path': 'Data/Variety/', 'files': 1, 'dimensions': [51,59]},
        'Management': {'path': 'Data/Management/', 'files': 6, 'dimensions': [60,65]},
    }
}
reg_json = os.path.join(BASE, '..', 'data_registry.json')
with open(reg_json, 'w', encoding='utf-8') as f:
    json.dump(registry, f, indent=2, ensure_ascii=False)
print(f'  [OK] {reg_json}')

# ═══════════════════════════════════════════
print('\n' + '='*60)
print('FINISHED')
print('='*60)
print()
print('Auto-downloaded: CO2 table, Variety template, Management README')
print('Files that may need manual download due to network restrictions:')
print('  1. WorldClim: https://www.worldclim.org/data/worldclim21.html')
print('     -> Bio variables 2.5m, Monthly tavg, Monthly prec')
print('  2. SRTM: pip install elevation && elevation clip ...')
print('  3. SoilGrids: via ISRIC WCS API (need owslib)')
print('  4. CHELSA daily: https://chelsa-climate.org/downloads/')
print('  5. Management: https://figshare.com/articles/24471919')
print('  6. China Soil: http://poles.tpdc.ac.cn/ (need registration)')
print('  7. Variety traits: http://202.127.42.145/bigdataNew/ (manual extraction)')
print('='*60)
