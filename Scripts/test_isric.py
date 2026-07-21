import urllib.request
urls = [
    'https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.vrt',
    'https://files.isric.org/soilgrids/latest/data/sand/sand_0-5cm_mean.vrt',
    'https://files.isric.org/soilgrids/latest/data/soc/soc_0-5cm_mean.vrt',
]
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        r = urllib.request.urlopen(req, timeout=15)
        cl = r.info().get('Content-Length', '?')
        name = url.split('/')[-2] + '/' + url.split('/')[-1]
        print(f'OK  {name}: {cl} bytes')
    except Exception as e:
        name = url.split('/')[-2]
        print(f'FAIL {name}: {e.__class__.__name__}')
