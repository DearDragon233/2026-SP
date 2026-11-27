p = r'D:\2026-SP\src\s5_figures_main\w57_study_area_map.py'
s = open(p, encoding='utf-8').read()
old = s[s.find("with rasterio.open(os.path.join(ROOT, \"Data\", \"CropArea_figshare\", \"CHN_2021.tif\")) as s:"):
        s.find("fig = plt.figure(figsize=(183*MM, 150*MM))")]
new = '''with rasterio.open(os.path.join(ROOT, "Data", "CropArea_figshare", "CHN_2021.tif")) as s:
    bi = list(s.descriptions).index("whea") + 1
    win = from_bounds(LON0, LAT0, LON1, LAT1, s.transform).round_offsets().round_lengths()
    raw = s.read(bi, window=win).astype(float)
    # The file carries no nodata tag but uses NaN for no-data (32.6% of the global
    # image); 0 means "data, no wheat"; >0 is wheat area in ha per 10 km cell.
    arr = np.where(np.isfinite(raw), raw, np.nan)
    b = rasterio.windows.bounds(win, s.transform)
    ext = (b[0], b[1], b[2], b[3])
    fin = arr[np.isfinite(arr)]
    print("window: %d cells | no-data %.1f%% | wheat>0 %.1f%% of valid cells | max %.0f ha/cell"
          % (arr.size, 100*np.isnan(arr).mean(), 100*(fin > 0).mean(), np.nanmax(arr)))
vmax = np.nanpercentile(arr, 99)

'''
assert s.find("with rasterio.open(os.path.join(ROOT, \"Data\", \"CropArea_figshare\", \"CHN_2021.tif\")) as s:") > 0
s = s.replace(old, new)
# drop the now-duplicated old extent/vmax lines that followed the block, if any remain
for dup in ["ext = (b[0], b[1], b[2], b[3])\n", "vmax = np.nanpercentile(arr, 99)\n", 'print("wheat area: max %.0f ha/cell, 99th pct %.0f" % (np.nanmax(arr), vmax))\n']:
    while s.count(dup) > 1:
        i = s.find(dup); s = s[:i] + s[i+len(dup):]
# masked array so NaN is transparent rather than pale yellow
s = s.replace('im = ax.imshow(arr, cmap="YlOrBr", vmin=0, vmax=vmax, extent=ext, origin="upper", interpolation="nearest", zorder=0)',
              'cmap = plt.get_cmap("YlOrBr").copy(); cmap.set_bad("white")\n'
              'im = ax.imshow(np.ma.masked_invalid(arr), cmap=cmap, vmin=0, vmax=vmax, extent=ext, origin="upper", interpolation="nearest", zorder=0)')
open(p, 'w', encoding='utf-8').write(s)
print("map script: NaN handled as no-data, extent from window bounds")
