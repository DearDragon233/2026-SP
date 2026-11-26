p = r'D:\2026-SP\src\s5_figures_main\w55_fix_fig1_fig2.py'
s = open(p, encoding='utf-8').read()
old_loop = '''    for ring in rings(f["geometry"]["coordinates"]):
        pts = np.array(ring)
        ax.plot(pts[:, 0], pts[:, 1], color=col, lw=1.0)'''
new_loop = '''    geom = shape(f["geometry"])
    polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        for ring in [poly.exterior] + list(poly.interiors):
            pts = np.array(ring.coords)
            ax.plot(pts[:, 0], pts[:, 1], color=col, lw=0.9 if ring is poly.exterior else 0.5)'''
assert old_loop in s
s = s.replace(old_loop, new_loop)
s = s.replace('import matplotlib.pyplot as plt\n', 'import matplotlib.pyplot as plt\nfrom shapely.geometry import shape\n', 1)
open(p, 'w', encoding='utf-8').write(s)
print('polygon extraction switched to shapely')
