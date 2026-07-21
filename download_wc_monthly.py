#!/usr/bin/env python
import urllib.request, os, zipfile, time

BASE = r'D:\2026-SP\Data'
WC_DIR = os.path.join(BASE, 'WorldClim')
os.makedirs(WC_DIR, exist_ok=True)

def dl(url, dest, desc):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f'  [SKIP] {desc}')
        return True
    print(f'  [DL] {desc}...')
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            with open(dest, 'wb') as f:
                f.write(data)
            print(f'  [OK] {desc}: {len(data)/1024/1024:.1f}MB')
            return True
        except Exception as e:
            if attempt < 2:
                print(f'  [RETRY] {e}')
                time.sleep(5)
    print(f'  [FAIL] {desc}')
    return False

# Monthly tavg
tavg_url = 'https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_tavg.zip'
tavg_zip = os.path.join(WC_DIR, 'WC_tavg_2.5m.zip')
if dl(tavg_url, tavg_zip, 'Monthly tavg'):
    with zipfile.ZipFile(tavg_zip, 'r') as z:
        z.extractall(WC_DIR)

# Monthly prec
prec_url = 'https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_prec.zip'
prec_zip = os.path.join(WC_DIR, 'WC_prec_2.5m.zip')
if dl(prec_url, prec_zip, 'Monthly prec'):
    with zipfile.ZipFile(prec_zip, 'r') as z:
        z.extractall(WC_DIR)

print('Done.')
