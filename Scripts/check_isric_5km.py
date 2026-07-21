import urllib.request

# 测试5km聚合数据 (WGS84, 适配WorldClim分辨率)
base = 'https://files.isric.org/soilgrids/latest/data_aggregated/5000m/'
props = ['clay', 'sand', 'silt', 'soc', 'bdod', 'cec', 'phh2o', 'nitrogen']
depth = '0-5cm'
stat = 'mean'

for prop in props:
    url = f'{base}{prop}/{prop}_{depth}_{stat}_5000.tif'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=30)
        cl = int(r.info().get('Content-Length', 0))
        print(f'OK  {prop}: {cl/1024/1024:.1f} MB')
    except Exception as e:
        print(f'FAIL {prop}: {e.__class__.__name__}')
