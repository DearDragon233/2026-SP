# -*- coding: utf-8 -*-
"""Pair audited yearbook rows with the same-year county aggregate of ChinaWheatYield30m."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = ROOT / "Data" / "external"
INPUT = EXTERNAL / "w41_county_wheat_statistics.csv"
DOWNLOAD = EXTERNAL / "ncp_yield_pairing" / "download"
OUTPUT = ROOT / "Outputs" / "reports"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, choices=range(2016, 2022))
    parser.add_argument("--raster", type=Path, help="A complete raster or a verified pilot subset for the selected year")
    parser.add_argument("--additional-stats", type=Path, help="Additional official statistics with area in ha")
    parser.add_argument("--only-additional", action="store_true", help="Pair only the official statistics provided explicitly")
    parser.add_argument("--output", type=Path, help="Save the results to this CSV path")
    args = parser.parse_args()
    if args.only_additional and not args.additional_stats:
        parser.error("--only-additional requires --additional-stats")
    raster = args.raster or DOWNLOAD / f"{args.year}ChinaWheatYield30m.tif"
    all_rows = []
    if not args.only_additional:
        with INPUT.open(encoding="utf-8-sig", newline="") as source:
            all_rows = list(csv.DictReader(source))
    if args.additional_stats:
        with args.additional_stats.open(encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                row["sown_mu"] = str(float(row["sown_ha"]) * 15)
                reported = row["reported_kg_ha"]
                row["reported_kg_per_mu"] = str(float(reported) / 15) if reported else ""
                all_rows.append(row)
    keys = [(row["province"], row["county"], row["harvest_year"]) for row in all_rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate yearbook county-year")
    for row in all_rows:
        area, production = float(row["sown_mu"]), float(row["production_t"])
        if not (np.isfinite(area) and np.isfinite(production) and min(area, production) > 0):
            raise ValueError(f"Source area and production must be positive: {row}")
        kg_mu = production * 1000 / area
        reported = row["reported_kg_per_mu"]
        if reported and abs(kg_mu - float(reported)) > 0.51:
            raise ValueError(f"Source area, output and yield are inconsistent: {row}")
    rows = [row for row in all_rows if int(row["harvest_year"]) == args.year]
    if not rows:
        raise ValueError(f"No yearbook rows available for {args.year}")

    collection = json.loads((DOWNLOAD / "geoBoundaries-CHN-ADM3.geojson").read_text(encoding="utf-8"))
    geometries = {item["properties"]["shapeID"]: item["geometry"] for item in collection["features"]}
    results = []
    with rasterio.open(raster) as src:
        if src.crs is None or src.crs.to_epsg() != 4326 or src.count != 1 or src.transform.b or src.transform.d:
            raise ValueError("Expected one north-up WGS84 yield band")
        for row in rows:
            shape = geometries[row["shape_id"]]
            window = geometry_window(src, [shape])
            transform = src.window_transform(window)
            values = src.read(1, window=window, masked=True)
            inside = geometry_mask([shape], out_shape=values.shape, transform=transform, invert=True)
            valid = inside & ~np.ma.getmaskarray(values) & np.isfinite(values.data) & (values.data > 0)
            pixels = int(valid.sum())
            total = int(inside.sum())
            latitude = np.radians(transform.f + transform.e * (np.arange(values.shape[0]) + 0.5))
            weights = np.broadcast_to(np.cos(latitude)[:, None], values.shape)
            avg = np.average(values.data[valid], weights=weights[valid]) if pixels else np.nan
            # Spherical pixel area at the equator, scaled by each row latitude.
            equatorial_pixel_ha = (
                6371008.8**2 * np.radians(abs(transform.a)) * 2 * np.sin(np.radians(abs(transform.e)) / 2)
            ) / 10000
            remote_area_ha = equatorial_pixel_ha * weights[valid].sum()
            stats_area_ha = float(row["sown_mu"]) / 15
            stats = float(row["production_t"]) * 15000 / float(row["sown_mu"])
            results.append({
                "province": row["province"], "county": row["county"], "harvest_year": args.year,
                "statistics_crop": row["source_crop"], "stats_kg_ha": f"{stats:.3f}",
                "remote_winter_wheat_kg_ha": f"{avg:.3f}" if pixels else "",
                "remote_minus_stats_kg_ha": f"{avg - stats:.3f}" if pixels else "",
                "county_pixel_centres": total, "positive_remote_pixel_centres": pixels,
                "stats_sown_ha": f"{stats_area_ha:.3f}", "remote_positive_ha": f"{remote_area_ha:.3f}",
                "remote_area_to_stats_sown_area": f"{remote_area_ha / stats_area_ha:.5f}",
                "scope_note": row["scope_note"], "shape_id": row["shape_id"],
            })
    dest = args.output or OUTPUT / f"w41_county_yield_pairing_{args.year}.csv"
    with dest.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=results[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(results)} pilot county-years to {dest.name}")


if __name__ == "__main__":
    main()
