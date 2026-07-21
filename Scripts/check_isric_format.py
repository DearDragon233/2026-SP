import urllib.request

# 先检查VRT里引用的实际tif路径
import xml.etree.ElementTree as ET
req = urllib.request.Request(
    'https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.vrt',
    headers={'User-Agent': 'Mozilla/5.0'})
r = urllib.request.urlopen(req, timeout=30)
content = r.read().decode()

# 找第一个SourceFilename
import re
sources = re.findall(r'<SourceFilename[^>]*>(.*?)</SourceFilename>', content)
print("VRT source files (first 5):")
for s in sources[:5]:
    print(f"  {s}")

# 测试实际tif
test_tifs = [
    'https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.tif',
    'https://files.isric.org/soilgrids/latest/data/clay/clay_0-5cm_mean.vrt',
]
for url in test_tifs:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Range': 'bytes=0-7'})
        r = urllib.request.urlopen(req, timeout=30)
        data = r.read(8)
        cl = r.info().get('Content-Length', '?')
        hex_start = data[:4].hex().upper()
        print(f"\n{url.split('/')[-1]}:")
        print(f"  Content-Length: {cl}")
        print(f"  First bytes: {hex_start}")
        print(f"  Supports Range: {'Accept-Ranges' in r.info()}")
    except Exception as e:
        print(f"\n{url.split('/')[-1]}: FAIL {e.__class__.__name__}")
