"""Measure sensitivity to eligibility rules and to a training-only label offset."""
import pandas as pd

from w41_pair_county_yield import OUTPUT
from w44_freeze_panel import KEY
from w45_label_swap import metrics, predictions


def main():
    panel = pd.read_csv(OUTPUT / "w44_frozen_panel.csv")
    folds = pd.read_csv(OUTPUT / "w44_folds.csv", dtype={"fold": str})
    primary = pd.read_csv(OUTPUT / "w45_primary_oof.csv", dtype={"fold": str})
    other = predictions(panel, folds.loc[folds.scenario.ne("primary")])
    all_predictions = pd.concat([primary, other], ignore_index=True)
    groups = ["scenario", "scheme", "training_label", "model"]
    key = ["scheme", "fold", *KEY]
    in_all = all_predictions.groupby(key)["scenario"].transform("nunique").eq(3)
    summary = pd.concat([
        metrics(all_predictions, groups).assign(evaluation_rows="all_scenario_test_rows"),
        metrics(all_predictions.loc[in_all], groups).assign(evaluation_rows="identical_test_rows"),
    ], ignore_index=True)
    summary.to_csv(OUTPUT / "w46_eligibility_metrics.csv", index=False, float_format="%.8f", lineterminator="\n")

    train = folds.loc[folds.scenario.eq("primary") & folds.role.eq("train")].merge(
        panel[KEY+["stats_kg_ha", "remote_winter_wheat_kg_ha"]], on=KEY, validate="many_to_one")
    train["offset"] = train.stats_kg_ha-train.remote_winter_wheat_kg_ha
    offset = train.groupby(["scheme", "fold"], as_index=False)["offset"].mean()
    corrected = primary.loc[primary.training_label.eq("remote")].merge(
        offset, on=["scheme", "fold"], validate="many_to_one")
    corrected["training_label"] = "remote_plus_paired_training_offset"
    corrected["error_kg_ha"] += corrected.offset
    metrics(pd.concat([primary, corrected]), groups).to_csv(
        OUTPUT / "w46_offset_diagnostic.csv", index=False, float_format="%.8f", lineterminator="\n")
    print(summary.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
