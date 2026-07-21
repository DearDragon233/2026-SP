#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib.request, json, csv, os, time

soil_dir = r'D:\2026-SP\Data\SoilGrids'
os.makedirs(soil_dir, exist_ok=True)

# Test single point first
print("=== Testing SoilGrids REST API ===")
for prop in ['sand','silt','clay','soc','nitrogen','phh2o','bdod','cec']:
    try:
        url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lon=116.5&lat=40.1&property={prop}&depth=0-5cm&value=mean'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        layers = data.get('properties',{}).get('layers',[])
        val = '?'
        if layers:
            depths = layers[0].get('depths',[])
            if depths:
                val = depths[0].get('values',{}).get('mean','?')
        print(f'  {prop}: mean={val}')
    except Exception as e:
        print(f'  {prop}: {e.__class__.__name__}: {str(e)[:80]}')

# Grid sampling across NCP
print("\n=== Grid sampling NCP (0.25-degree) ===")
props = ['sand','silt','clay','soc','nitrogen','phh2o','bdod','cec']
samples = []
lats = [33, 34, 35, 36, 37, 38, 39, 40]
lons = [112, 114, 116, 118, 120]

for lat in lats:
    for lon in lons:
        sample = {'lat': lat, 'lon': lon}
        for prop in props:
            try:
                url = f'https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}&property={prop}&depth=0-5cm&value=mean'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = json.loads(r.read())
                layers = data.get('properties',{}).get('layers',[])
                val = None
                if layers:
                    depths = layers[0].get('depths',[])
                    if depths:
                        val = depths[0].get('values',{}).get('mean',None)
                sample[prop] = val
            except Exception as e:
                sample[prop] = None
            time.sleep(0.3)
        samples.append(sample)
        soc_val = sample.get('soc','?')
        sand_val = sample.get('sand','?')
        ph_val = sample.get('phh2o','?')
        print(f'  ({lat}N,{lon}E): sand={sand_val}, soc={soc_val}, pH={ph_val}')

# Save CSV
csv_path = os.path.join(soil_dir, 'SG_NCP_0.25deg_Samples.csv')
with open(csv_path, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['lat','lon']+props)
    w.writeheader()
    w.writerows(samples)
print(f'\nSaved: {csv_path} ({os.path.getsize(csv_path)} bytes)')
print('This CSV can be interpolated to 1km grid using scipy.interpolate.griddata')
