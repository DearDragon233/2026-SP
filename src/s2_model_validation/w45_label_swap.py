"""Run identical fold-local models on statistics and remote-sensing training labels."""
import argparse

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from w41_pair_county_yield import OUTPUT
from w44_build_fingerprints import FEATURES
from w44_freeze_panel import KEY, SCENARIOS

LABELS = {"statistics": "stats_kg_ha", "remote": "remote_winter_wheat_kg_ha"}


def model_set():
    return {
        "mean": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1)),
        "random_forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1),
    }


def predictions(panel, folds, features=FEATURES):
    indexed = panel.set_index(KEY)
    if not indexed.index.is_unique:
        raise ValueError("Panel contains duplicate county-year keys")
    output = []
    for (scenario, scheme, fold), assignment in folds.groupby(["scenario", "scheme", "fold"], sort=False):
        train = indexed.loc[pd.MultiIndex.from_frame(assignment.loc[assignment.role.eq("train"), KEY])]
        test = indexed.loc[pd.MultiIndex.from_frame(assignment.loc[assignment.role.eq("test"), KEY])]
        for label, column in LABELS.items():
            for name, model in model_set().items():
                model.fit(train[list(features)], train[column])
                result = test.reset_index()[KEY+["province", "county", "stats_kg_ha"]].copy()
                result = result.assign(scenario=scenario, scheme=scheme, fold=fold, training_label=label, model=name,
                                       prediction_kg_ha=model.predict(test[list(features)]), train_rows=len(train))
                result["error_kg_ha"] = result.prediction_kg_ha - result.stats_kg_ha
                output.append(result)
    return pd.concat(output, ignore_index=True)


def metrics(out, by):
    groups = out.assign(abs_error=out.error_kg_ha.abs(), squared=out.error_kg_ha ** 2).groupby(by, sort=True)
    summary = groups.agg(test_rows=("error_kg_ha", "size"), mae_kg_ha=("abs_error", "mean"),
                         mse_kg2_ha2=("squared", "mean"), bias_kg_ha=("error_kg_ha", "mean")).reset_index()
    summary["rmse_kg_ha"] = np.sqrt(summary.pop("mse_kg2_ha2"))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="primary")
    args = parser.parse_args()
    panel = pd.read_csv(OUTPUT / "w44_frozen_panel.csv")
    folds = pd.read_csv(OUTPUT / "w44_folds.csv", dtype={"fold": str})
    out = predictions(panel, folds.loc[folds.scenario.eq(args.scenario)])
    fields = ["scenario", "scheme", "training_label", "model"]
    stem = OUTPUT / f"w45_{args.scenario}"
    out.to_csv(str(stem)+"_oof.csv", index=False, float_format="%.8f", lineterminator="\n")
    metrics(out, fields+["fold"]).to_csv(str(stem)+"_fold_metrics.csv", index=False, float_format="%.8f", lineterminator="\n")
    summary = metrics(out, fields)
    summary.to_csv(str(stem)+"_metrics.csv", index=False, float_format="%.8f", lineterminator="\n")
    print(summary.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
