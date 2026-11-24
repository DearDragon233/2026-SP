"""Evaluate development-only models against frozen Pingdingshan county statistics."""
import pandas as pd

from w44_build_fingerprints import FEATURES, OUTPUT
from w44_freeze_panel import KEY
from w45_label_swap import metrics, predictions
from w48_freeze_pds import COHORT

GROUPS = ["training_label", "model"]
PREDICTIONS = OUTPUT / "w49_pds_oof.csv"


def main():
    development = pd.read_csv(OUTPUT / "w44_frozen_panel.csv")
    development = development.loc[development.primary]
    cohort = pd.read_csv(COHORT)
    test = cohort.loc[cohort.unscreened]
    if test.empty or set(test.shape_id) & set(development.shape_id):
        raise ValueError("Missing or overlapping geographic holdout")
    assignments, diagnoses = [], []
    for year, held in test.groupby("harvest_year"):
        train = development.loc[development.harvest_year.lt(year)]
        if train.harvest_year.nunique() < 2:
            raise ValueError(f"Insufficient prior development years for {year}")
        for role, frame in (("train", train), ("test", held)):
            assignments.append(frame[KEY].assign(scenario="primary_training", scheme="pds_and_future", fold=year, role=role))
        below = held[list(FEATURES)].lt(train[list(FEATURES)].min())
        above = held[list(FEATURES)].gt(train[list(FEATURES)].max())
        outside = (below | above)
        diagnoses.append(held[KEY+["weather_series_id", "remote_area_to_stats_sown_area", "primary", "strict"]].assign(
            n_outside=outside.sum(axis=1),
            outside_features=outside.apply(lambda row: "|".join(row.index[row]), axis=1)))
    folds = pd.concat(assignments, ignore_index=True)
    panel = pd.concat([development, test], ignore_index=True)
    out = predictions(panel, folds).merge(pd.concat(diagnoses), on=KEY, validate="many_to_one")
    if not out.groupby(KEY).size().eq(6).all():
        raise ValueError("Unpaired held-out predictions")
    out.to_csv(PREDICTIONS, index=False, float_format="%.8f", lineterminator="\n")
    folds.to_csv(OUTPUT / "w49_pds_folds.csv", index=False, lineterminator="\n")
    aggregate = metrics(out.loc[out.primary], GROUPS).assign(harvest_year="all")
    yearly = metrics(out.loc[out.primary], ["harvest_year", *GROUPS])
    summary = pd.concat([aggregate, yearly], ignore_index=True)
    summary.to_csv(OUTPUT / "w49_pds_primary_metrics.csv", index=False, float_format="%.8f", lineterminator="\n")
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
