#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Download all public data to D:\\2026-SP\\Data\\
Run: python download_data.py
"""

import os, sys, urllib.request, zipfile, csv, subprocess

BASE = r'D:\2026-SP\Data'
os.makedirs(BASE, exist_ok=True)

def download_file(url, dest_path, desc=''):
    """Download a file with progress reporting."""
    if os.path.exists(dest_path):
        print(f'  [SKIP] {desc} already exists: {dest_path}')
        return True
    print(f'  [DOWNLOAD] {desc} ...')
    try:
        urllib.request.urlretrieve(url, dest_path)
        sz = os.path.getsize(dest_path)
        print(f'  [OK] {desc}: {sz/1024/1024:.1f} MB -> {dest_path}')
        return True
    except Exception as e:
        print(f'  [FAIL] {desc}: {e}')
        return False

# ═══════════════════════════════════════════
# 1. WorldClim 2.1 bio variables (10 arc-minute for speed, ~2.5 arc-min available too)
#    Using 2.5 arc-minute (~5km) as a faster test, or 30 arc-second (~1km) for final
# ═══════════════════════════════════════════
WC_DIR = os.path.join(BASE, 'WorldClim')
os.makedirs(WC_DIR, exist_ok=True)

# WorldClim 2.1 historical climate: bio variables at 2.5 arc-minutes (~5km)
# Full download from: https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_bio.zip
WC_BIO_URL = 'https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_bio.zip'
WC_BIO_ZIP = os.path.join(WC_DIR, 'WC_bio_2.5m.zip')

print('\n=== 1. WorldClim Bio Variables (19 files) ===')
if not os.path.exists(WC_BIO_ZIP):
    download_file(WC_BIO_URL, WC_BIO_ZIP, 'WorldClim bio variables zip')
    # Extract
    print('  [EXTRACT] WorldClim bio variables ...')
    with zipfile.ZipFile(WC_BIO_ZIP, 'r') as zf:
        zf.extractall(WC_DIR)

# WorldClim monthly average temperature  
WC_TAVG_URL = 'https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_tavg.zip'
WC_TAVG_ZIP = os.path.join(WC_DIR, 'WC_tavg_2.5m.zip')
if not os.path.exists(WC_TAVG_ZIP):
    download_file(WC_TAVG_URL, WC_TAVG_ZIP, 'WorldClim monthly tavg zip')
    with zipfile.ZipFile(WC_TAVG_ZIP, 'r') as zf:
        zf.extractall(WC_DIR)

# WorldClim monthly precipitation
WC_PREC_URL = 'https://biogeo.ucdavis.edu/data/worldclim/v2.1/base/wc2.1_2.5m_prec.zip'
WC_PREC_ZIP = os.path.join(WC_DIR, 'WC_prec_2.5m.zip')
if not os.path.exists(WC_PREC_ZIP):
    download_file(WC_PREC_URL, WC_PREC_ZIP, 'WorldClim monthly prec zip')
    with zipfile.ZipFile(WC_PREC_ZIP, 'r') as zf:
        zf.extractall(WC_DIR)

# ═══════════════════════════════════════════
# 2. SRTM 30m DEM for Pinggu area
#    Using CGIAR SRTM tiles covering Beijing area
# ═══════════════════════════════════════════
SRTM_DIR = os.path.join(BASE, 'SRTM')
os.makedirs(SRTM_DIR, exist_ok=True)

print('\n=== 2. SRTM Elevation Data ===')
# SRTM tile for Beijing area: lat 40, lon 115 (n40e116 covers Pinggu)
# CGIAR SRTM: http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/
SRTM_TILES = [
    ('srtm_58_05.zip', 'n40e116'),  # Covers Pinggu area
    ('srtm_58_06.zip', 'n40e117'),  # Adjacent tile
]
SRTM_BASE_URL = 'http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/'

for fname, tilename in SRTM_TILES:
    url = SRTM_BASE_URL + fname
    dest = os.path.join(SRTM_DIR, f'Srtm_{tilename}.zip')
    if not os.path.exists(dest):
        download_file(url, dest, f'SRTM tile {tilename}')
        if os.path.exists(dest):
            with zipfile.ZipFile(dest, 'r') as zf:
                zf.extractall(SRTM_DIR)

# ═══════════════════════════════════════════
# 3. CO2 Concentration CSV
# ═══════════════════════════════════════════
CMIP6_DIR = os.path.join(BASE, 'CMIP6')
os.makedirs(CMIP6_DIR, exist_ok=True)

print('\n=== 3. CO2 Concentration Reference ===')
co2_csv = os.path.join(CMIP6_DIR, 'CMIP6_CO2_Concentration.csv')
with open(co2_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Year', 'SSP', 'CO2_ppm'])
    # SSP2-4.5 values (approximate from CMIP6 ScenarioMIP)
    co2_ssp245 = {2020:412, 2030:440, 2040:468, 2050:490, 2060:513, 2070:530, 2080:543, 2090:550, 2100:555}
    co2_ssp585 = {2020:412, 2030:448, 2040:492, 2050:540, 2060:602, 2070:670, 2080:750, 2090:840, 2100:935}
    for yr in sorted(co2_ssp245.keys()):
        w.writerow([yr, 'SSP2-4.5', co2_ssp245[yr]])
    for yr in sorted(co2_ssp585.keys()):
        w.writerow([yr, 'SSP5-8.5', co2_ssp585[yr]])
print(f'  [OK] CO2 reference table: {co2_csv}')

# ═══════════════════════════════════════════
# 4. Variety template CSV
# ═══════════════════════════════════════════
VARIETY_DIR = os.path.join(BASE, 'Variety')
os.makedirs(VARIETY_DIR, exist_ok=True)

print('\n=== 4. Variety Trait Template ===')
variety_csv = os.path.join(VARIETY_DIR, 'Variety_Wheat_Traits_Template.csv')
with open(variety_csv, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['Variety_Name', 'Approval_Year', 'Region', 'Maturity_Days',
                'GrainFill_Days', 'TKW_g', 'GrainPerSpike', 'SpikeDensity_w_per_ha',
                'PlantHeight_cm', 'ColdTolerance_1to5', 'DroughtTolerance_1to5',
                'Yield_Mg_ha', 'Notes'])
    # Sample rows for reference
    w.writerow(['济麦22', '2006', '山东', '', '', '', '', '', '', '', '', '', '待从审定公告提取'])
    w.writerow(['中麦175', '2009', '北京', '', '', '', '', '', '', '', '', '', '待从审定公告提取'])
    w.writerow(['农大211', '2007', '北京', '', '', '', '', '', '', '', '', '', '待从审定公告提取'])
    w.writerow(['京冬8号', '1999', '北京', '', '', '', '', '', '', '', '', '', '待从审定公告提取'])
    w.writerow(['石4185', '2000', '河北', '', '', '', '', '', '', '', '', '', '待从审定公告提取'])
print(f'  [OK] Variety template: {variety_csv}')

# ═══════════════════════════════════════════
# 5. Management labels placeholder
# ═══════════════════════════════════════════
MGMT_DIR = os.path.join(BASE, 'Management')
os.makedirs(MGMT_DIR, exist_ok=True)

print('\n=== 5. Management Data Placeholder ===')
mgmt_readme = os.path.join(MGMT_DIR, 'README.txt')
with open(mgmt_readme, 'w', encoding='utf-8') as f:
    f.write('Management optimization data from Xiao et al. (2024) Nature Food 5:59-71\n')
    f.write('Download from: https://figshare.com/articles/24471919\n')
    f.write('Files expected:\n')
    f.write('  - N_wheat_optimized.tif\n')
    f.write('  - N_maize_optimized.tif\n')
    f.write('  - Irr_wheat_optimized.tif\n')
    f.write('  - Irr_maize_optimized.tif\n')
    f.write('  - Res_wheat_optimized.tif\n')
    f.write('  - Res_maize_optimized.tif\n')
print(f'  [OK] Management README: {mgmt_readme}')
print(f'  NOTE: Please visit https://figshare.com/articles/24471919 to download')
print(f'        the optimized management map data from Xiao et al. (2024).')

# ═══════════════════════════════════════════
# Final summary
# ═══════════════════════════════════════════
print('\n' + '='*60)
print('DOWNLOAD SUMMARY')
print('='*60)
print(f'Base directory: {BASE}')
for root, dirs, files in os.walk(BASE):
    level = root.replace(BASE, '').count(os.sep)
    indent = '  ' * level
    print(f'{indent}{os.path.basename(root)}/')
    sub_indent = '  ' * (level + 1)
    for f in files[:5]:
        sz = os.path.getsize(os.path.join(root, f))
        print(f'{sub_indent}{f} ({sz/1024:.0f} KB)')
    if len(files) > 5:
        print(f'{sub_indent}... and {len(files)-5} more files')
print('='*60)
print('Next manual steps:')
print('  1. Download management data from https://figshare.com/articles/24471919')
print('  2. Register at http://poles.tpdc.ac.cn/ for China Soil Database')
print('  3. Download CHELSA daily data from https://chelsa-climate.org/downloads/')
print('  4. Manually extract variety traits from http://202.127.42.145/bigdataNew/')
