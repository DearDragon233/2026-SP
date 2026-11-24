"""Acquire only the TIFF byte ranges needed for the selected study counties."""
import argparse
import csv
import hashlib
import json
import math
import re
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import rasterio
from rasterio.features import geometry_window

from w41_pair_county_yield import DOWNLOAD, EXTERNAL, INPUT, OUTPUT

SOURCES = (INPUT, EXTERNAL / "w42_sjz_winter_wheat.csv")
HEADER_BYTES = 2_500_000


def read_range(url, start, stop, expected_size=None):
    result = subprocess.run(
        ["curl", "-fsSL", "--retry", "2", "--connect-timeout", "12", "--max-time", "50",
         "--max-filesize", str(stop - start), "--range", f"{start}-{stop-1}",
         "--write-out", "%{http_code}|%header{content-range}", url],
        capture_output=True, check=True,
    )
    body, response = result.stdout[:stop-start], result.stdout[stop-start:]
    match = re.fullmatch(rb"206\|bytes (\d+)-(\d+)/(\d+)", response)
    if not match:
        raise ValueError(f"Unverified response for {start}-{stop-1}: {response[:80]!r}")
    first, last, size = map(int, match.groups())
    if (first, last) != (start, stop-1) or (expected_size is not None and size != expected_size):
        raise ValueError(f"Unexpected byte interval: {response!r}")
    return body, size


def tile_ranges(header, src, geometries):
    if header[:4] != b"II*\x00":
        raise ValueError("Expected a little-endian classic TIFF")
    pointer, = struct.unpack_from("<I", header, 4)
    count, = struct.unpack_from("<H", header, pointer)
    tags = dict((tag, (kind, count, value)) for tag, kind, count, value in (
        struct.unpack_from("<HHII", header, pointer+2+12*i) for i in range(count)))
    heights, widths = src.block_shapes[0]
    tile_columns = math.ceil(src.width / widths)
    for tag in (324, 325):
        kind, count, offset = tags[tag]
        if kind != 4 or count != tile_columns * math.ceil(src.height / heights) or offset + 4*count > len(header):
            raise ValueError("Tile table not contained in the source header")
    start_table, length_table = tags[324][2], tags[325][2]
    tiles = set()
    for geometry in geometries:
        window = geometry_window(src, [geometry])
        for row in range(int(window.row_off)//heights, math.ceil((window.row_off+window.height)/heights)):
            for col in range(int(window.col_off)//widths, math.ceil((window.col_off+window.width)/widths)):
                tile = row * tile_columns + col
                start, = struct.unpack_from("<I", header, start_table+4*tile)
                length, = struct.unpack_from("<I", header, length_table+4*tile)
                if length and start+length > len(header):
                    tiles.add((max(start, len(header)), start+length))
    merged = []
    for first, last in sorted(tiles):
        if merged and first-merged[-1][1] <= 65_536 and last-merged[-1][0] <= 4_000_000:
            merged[-1] = (merged[-1][0], max(merged[-1][1], last))
        else:
            merged.append((first, last))
    return merged


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, choices=range(2016, 2022))
    parser.add_argument("--statistics", type=Path, action="append", help="Use these county-year CSVs instead of the pilot inputs")
    parser.add_argument("--prefix", default="w43", help="Prefix for the local subset and its verification manifest")
    args = parser.parse_args()
    year = args.year
    ids = set()
    for source in args.statistics or SOURCES:
        with source.open(encoding="utf-8-sig", newline="") as data:
            ids.update(r["shape_id"] for r in csv.DictReader(data) if int(r["harvest_year"]) == year)
    if not ids:
        raise ValueError(f"No county observations for {year}")
    collection = json.loads((DOWNLOAD / "geoBoundaries-CHN-ADM3.geojson").read_text(encoding="utf-8"))
    shapes = {f["properties"]["shapeID"]: f["geometry"] for f in collection["features"]}
    url = f"https://zenodo.org/records/7360753/files/{year}ChinaWheatYield30m.tif?download=1"
    header, size = read_range(url, 0, HEADER_BYTES)
    with rasterio.MemoryFile(header) as memory, memory.open() as src:
        if src.crs is None or src.crs.to_epsg() != 4326 or src.count != 1:
            raise ValueError(f"Tile header lacks the expected WGS84 georeferencing for {year}")
        ranges = tile_ranges(header, src, [shapes[key] for key in sorted(ids)])
    print(f"{year}: {len(ids)} counties, {len(ranges)} intervals, {sum(b-a for a,b in ranges):,} bytes", flush=True)

    def fetch(bounds):
        start, stop = bounds
        body, _ = read_range(url, start, stop, size)
        return start, body

    def write_range(dest, records, start, body):
        dest.seek(start)
        dest.write(body)
        records.append({"start": start, "end_exclusive": start+len(body), "sha256": hashlib.sha256(body).hexdigest()})

    dest = DOWNLOAD / f"{args.prefix}_{year}_counties.sparse.tif"
    partial = dest.with_suffix(".part")
    records = []
    with partial.open("wb") as file, ThreadPoolExecutor(max_workers=4) as pool:
        file.truncate(size)
        write_range(file, records, 0, header)
        for start, body in pool.map(fetch, ranges):
            write_range(file, records, start, body)
    partial.replace(dest)
    manifest = {"source": url, "size_bytes": size, "shape_ids": sorted(ids), "byte_ranges": records}
    (OUTPUT / f"{args.prefix}_remote_windows_{year}.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
