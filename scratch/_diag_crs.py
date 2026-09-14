import rasterio
for p in [r"D:\2026-SP\Data\SoilGrids_wgs84\clay_0-5cm_mean_5000.tif",
          r"D:\2026-SP\Data\WorldClim\wc2.1_2.5m_bio_1.tif",
          r"D:\2026-SP\Data\SRTM\srtm_60_04.tif"]:
    with rasterio.open(p) as s:
        print(p.split(chr(92))[-1])
        print("  crs:", s.crs, "| epsg:", s.crs.to_epsg())
        print("  bounds:", s.bounds)
        print("  res:", s.res, "| size:", s.width, "x", s.height)
        print("  nodata:", s.nodata)
