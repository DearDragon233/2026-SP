"""Build the fixed geographic holdout using the W44 feature definitions."""
import hashlib
import json

import pandas as pd

from w44_build_fingerprints import DOWNLOAD, EXTERNAL, FEATURES, OUTPUT, daily_weather, fingerprint
from w44_freeze_panel import KEY

STATS = EXTERNAL / "w47_pds_wheat_statistics.csv"
COHORT = OUTPUT / "w48_pds_frozen.csv"


def main():
    stats = pd.read_csv(STATS)
    collection = json.loads((DOWNLOAD / "geoBoundaries-CHN-ADM3.geojson").read_text(encoding="utf-8"))
    shapes = {item["properties"]["shapeID"]: item["geometry"] for item in collection["features"]}
    weather, sources = [], []
    for shape_id, rows in stats.groupby("shape_id"):
        (lon, lat), days, (path, raw, url, sha256) = daily_weather(shape_id, shapes[shape_id])
        if raw is not None:
            path.write_bytes(raw)
        signature = hashlib.sha256(json.dumps(days, sort_keys=True).encode()).hexdigest()[:16]
        for year in rows.harvest_year:
            weather.append((shape_id, year, lon, lat, signature, *fingerprint(days, year)))
        sources.append({"shape_id": shape_id, "url": url, "sha256": sha256})
    weather = pd.DataFrame(weather, columns=[*KEY, "longitude", "latitude", "weather_series_id", *FEATURES])
    pairing = pd.concat([pd.read_csv(OUTPUT / f"w48_pds_pairing_{year}.csv")
                         for year in sorted(stats.harvest_year.unique())], ignore_index=True)
    panel = pairing.merge(weather, on=KEY, how="outer", validate="one_to_one", indicator=True)
    if len(panel) != len(stats) or not panel._merge.eq("both").all():
        raise ValueError("Statistical, remote and weather county-year keys disagree")
    panel = panel.drop(columns="_merge")
    ratio = panel.remote_area_to_stats_sown_area
    panel["unscreened"] = panel.positive_remote_pixel_centres.gt(0)
    panel["primary"] = panel.unscreened & ratio.between(2/3, 1.5)
    panel["strict"] = panel.unscreened & ratio.between(0.8, 1.25)
    panel["exclusion_reason"] = ""
    panel.loc[~panel.primary, "exclusion_reason"] = "outside_primary_area_ratio"
    panel.loc[~panel.unscreened, "exclusion_reason"] = "no_positive_remote_pixels"
    development = pd.read_csv(OUTPUT / "w44_frozen_panel.csv")
    for column in ("shape_id", "weather_series_id"):
        if set(panel[column]) & set(development[column]):
            raise ValueError(f"External and development sets overlap on {column}")
    if min(panel.harvest_year) < 2019:
        raise ValueError("External test must follow at least two development harvest years")
    panel.sort_values(["harvest_year", "shape_id"]).to_csv(
        COHORT, index=False, float_format="%.8f", lineterminator="\n")
    (OUTPUT / "w48_pds_power_sources.json").write_text(json.dumps(sources, indent=2)+"\n", encoding="utf-8")
    print(panel.groupby("harvest_year")[["unscreened", "primary", "strict"]].sum().to_string())


if __name__ == "__main__":
    main()
