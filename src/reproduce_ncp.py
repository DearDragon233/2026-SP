"""Regenerate the North China pilot results from the committed frozen inputs."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    inputs = (
        "w44_frozen_panel.csv",
        "w44_folds.csv",
        "w48_pds_frozen.csv",
    )
    for name in inputs:
        path = ROOT / "Outputs" / "reports" / name
        if not path.is_file():
            raise SystemExit(f"Missing frozen input: {path}")

    scripts = (
        "s2_model_validation/w45_label_swap.py",
        "s2_model_validation/w46_check_sensitivity.py",
        "s2_model_validation/w49_test_pds.py",
        "s2_model_validation/w50_diagnose_pds.py",
        "s5_figures_main/w51_plot_pds_transfer.py",
    )
    for script in scripts:
        print(f"Running {script}", flush=True)
        result = subprocess.run([sys.executable, str(ROOT / "src" / script)], cwd=ROOT)
        if result.returncode:
            raise SystemExit(f"{script} failed with exit status {result.returncode}")


if __name__ == "__main__":
    main()
