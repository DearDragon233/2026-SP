"""Measure paired error differences and their sensitivity to held-out cases."""
import pandas as pd

from w44_build_fingerprints import OUTPUT
from w44_freeze_panel import KEY
from w45_label_swap import metrics
from w49_test_pds import GROUPS, PREDICTIONS


def main():
    out = pd.read_csv(PREDICTIONS)
    primary = out.loc[out.primary]
    strata = {
        "primary": primary,
        "strict": out.loc[out.strict],
        "unscreened": out,
        "inside_training_range": primary.loc[primary.n_outside.eq(0)],
        "outside_training_range": primary.loc[primary.n_outside.gt(0)],
    }
    summary = pd.concat([metrics(rows, GROUPS).assign(stratum=name)
                         for name, rows in strata.items() if not rows.empty], ignore_index=True)
    summary.to_csv(OUTPUT / "w50_pds_strata.csv", index=False, float_format="%.8f", lineterminator="\n")

    membership = primary[[*KEY, "weather_series_id"]].drop_duplicates()
    errors = primary.assign(absolute_error=primary.error_kg_ha.abs()).pivot(
        index=KEY, columns=GROUPS, values="absolute_error")
    comparisons = {
        ("ridge", "remote_minus_statistics"): errors["remote", "ridge"] - errors["statistics", "ridge"],
        ("mean", "remote_minus_statistics"): errors["remote", "mean"] - errors["statistics", "mean"],
        ("random_forest", "remote_minus_statistics"): errors["remote", "random_forest"] - errors["statistics", "random_forest"],
        **{(model, f"{label}_minus_same_label_mean"): errors[label, model] - errors[label, "mean"]
           for label in ("statistics", "remote") for model in ("ridge", "random_forest")},
    }
    result = []
    for (model, comparison), effect in comparisons.items():
        paired = membership.merge(effect.rename("difference").reset_index(), on=KEY, validate="one_to_one")
        result.append((model, comparison, "all", "", len(paired), paired.difference.mean()))
        for column in ("harvest_year", "weather_series_id", "shape_id"):
            for omitted in sorted(paired[column].unique()):
                kept = paired.loc[paired[column].ne(omitted)]
                if len(kept):
                    result.append((model, comparison, column, omitted, len(kept), kept.difference.mean()))
    report = pd.DataFrame(result, columns=[
        "model", "comparison", "omission_unit", "omitted", "test_rows", "mae_difference_kg_ha"])
    report.to_csv(OUTPUT / "w50_pds_paired_differences.csv", index=False, float_format="%.8f", lineterminator="\n")
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
