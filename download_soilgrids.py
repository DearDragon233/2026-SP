#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download SoilGrids 2.0 data for NCP via WCS API"""
import os, sys
import numpy as np

soil_dir = r'D:\2026-SP\Data\SoilGrids'
os.makedirs(soil_dir, exist_ok=True)

# SoilGrids properties we need (0-5cm layer)
properties = {
    'sand':     ('sand_0-5cm_mean',     'SG_Sand_0-5cm_wt.tif'),
    'silt':     ('silt_0-5cm_mean',     'SG_Silt_0-5cm_wt.tif'),
    'clay':     ('clay_0-5cm_mean',     'SG_Clay_0-5cm_wt.tif'),
    'soc':      ('soc_0-5cm_mean',      'SG_SOC_0-5cm_dgkg.tif'),
    'nitrogen': ('nitrogen_0-5cm_mean', 'SG_Nitrogen_0-5cm_cgkg.tif'),
    'phh2o':    ('phh2o_0-5cm_mean',    'SG_pH_0-5cm_x10.tif'),
    'bdod':     ('bdod_0-5cm_mean',     'SG_BD_0-5cm_cgcm3.tif'),
    'cec':      ('cec_0-5cm_mean',      'SG_CEC_0-5cm_mmolc.tif'),
}

try:
    from owslib.wcs import WebCoverageService
except ImportError:
    print('[FAIL] owslib not installed. pip install owslib')
    sys.exit(1)

# Try the WCS API for each property
for prop_name, (layer_id, out_filename) in properties.items():
    out_path = os.path.join(soil_dir, out_filename)
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f'[SKIP] {prop_name} exists')
        continue
    
    print(f'[TRY] {prop_name} ({layer_id})...')
    try:
        wcs_url = f'https://maps.isric.org/mapserv?map=/map/{prop_name}.map'
        wcs = WebCoverageService(wcs_url, version='2.0.1', timeout=120)
        
        # Get coverage for NCP bbox
        response = wcs.getCoverage(
            identifier=[layer_id],
            bbox=(110, 32, 122, 40),  # NCP extent
            format='image/tiff',
            width=480,   # ~12 degrees / 0.025 deg per pixel
            height=320,
            crs='urn:ogc:def:crs:EPSG::4326'
        )
        data = response.read()
        with open(out_path, 'wb') as f:
            f.write(data)
        print(f'  [OK] {prop_name}: {len(data)/1024:.0f} KB')
    except Exception as e:
        print(f'  [FAIL] {prop_name}: {e.__class__.__name__}: {str(e)[:200]}')
        # Try alternative: direct download from files.isric.org
        print(f'  [ALT] Trying HTTP direct download...')
        try:
            import urllib.request
            alt_url = f'https://files.isric.org/soilgrids/latest/data/{prop_name}/{prop_name}_0-5cm_mean.vrt'
            req = urllib.request.Request(alt_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                vrt_data = r.read()
            vrt_path = os.path.join(soil_dir, f'SG_{prop_name}_0-5cm.vrt')
            with open(vrt_path, 'wb') as f:
                f.write(vrt_data)
            print(f'  [OK-alt] VRT file: {len(vrt_data)/1024:.0f} KB (use GDAL to extract bbox)')
        except Exception as e2:
            print(f'  [FAIL-alt] {e2.__class__.__name__}')

print('\nDone.')
