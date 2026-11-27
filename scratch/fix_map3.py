p = r'D:\2026-SP\src\s5_figures_main\w57_study_area_map.py'
s = open(p, encoding='utf-8').read()
old = '''    b = rasterio.windows.bounds(win, s.transform)
    ext = (b[0], b[1], b[2], b[3])'''
new = '''    # rasterio.windows.bounds returns (left, bottom, right, top);
    # imshow wants (left, right, bottom, top).
    left, bottom, right, top = rasterio.windows.bounds(win, s.transform)
    ext = (left, right, bottom, top)'''
assert old in s, "extent block not found"
s = s.replace(old, new)
open(p, 'w', encoding='utf-8').write(s)
print("extent order fixed: (left, right, bottom, top)")
