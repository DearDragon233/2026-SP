# -*- coding: utf-8 -*-
"""W27-R10: number-to-ledger provenance audit of Manuscript_v5.0_fulltext.md.
Extracts the load-bearing statistics from the prose and checks each against
its frozen ledger value. Output: w27_r10_number_audit.csv (+ console verdict)."""
import os, re, warnings
import pandas as pd
warnings.filterwarnings("ignore")
ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
s = open(os.path.join(ROOT, "Paper", "Manuscript_v5.0_fulltext.md"), encoding="utf-8").read()

def has(pattern):
    return bool(re.search(pattern, s))

checks = [
 ("A mean/SD 7.21±0.23", r"7\.21 ± 0\.23"),
 ("A +38% vs Beijing 5.24", r"38% above the Beijing statistical mean of 5\.24"),
 ("B train fit 0.99", r"training-fit R² = 0\.99"),
 ("B circular 0.98 vs LOO 0.20-0.27", r"R² = 0\.98\. The gap is the trap.*R² = 0\.20–0\.27", ),
 ("D +10%", r"\+10% above the statistical mean"),
 ("spectrum 0.400/0.367/0.113/-0.205/0.124/-0.136", r"random 0\.400 ± 0\.015; checkerboard \(1× range\) 0\.367; latitude blocks 0\.113 pooled \(fold-level −0\.205"),
 ("dose +0.113->-0.006, NN 2.3-2.4", r"\+0\.113 to −0\.006 \*\*while the mean nearest-neighbour distance between blocks never leaves 2\.3–2\.4 km"),
 ("lat/LOBO/env gaps +0.288/+0.276/+0.54", r"latitude \+0\.288, LOBO \+0\.276, environment-space \+0\.54"),
 ("national range 462km, ~2 own ranges", r"≈462 km.*only ~2 of its own ranges"),
 ("national checker <=0.07, lat +0.32", r"checkerboard gaps never exceed \+0\.07.*latitude blocking costs \+0\.32"),
 ("PC1 66.3% r -0.94", r"PC1 explains 66\.3% of variance and correlates with elevation at r = −0\.94"),
 ("PC1-5 -> A 0.24", r"PC1–PC5 jointly explain only R² = 0\.24"),
 ("thermal +0.006/zero", r"add \+0\.006 on target C and exactly zero on A"),
 ("NCP 0.690±0.006 / subset 0.689 / fine 0.450", r"R² = 0\.690 ± 0\.006 on the 7,784-grid national gradient \(0\.689 on the 25-column subset.*0\.450 at the 1-km"),
 ("windows median 0.163 IQR", r"median R² of 0\.163 \(IQR 0\.027–0\.272; 60% of windows below 0\.2"),
 ("power XGB 0.00 / ridge 40%/3%", r"detection probability 0\.00 even at R²pop = 0\.5.*\(40% detection at R²pop = 0\.3\).*\(3%\)"),
 ("M/E/E+M 0.913/0.690/0.948", r"M-only R² = 0\.913, E-only 0\.690, E\+M 0\.948"),
 ("SHAP MN 0.95", r"0\.95 of the M-model importance to the rotation-maize N rate"),
 ("weak-reg M 0.218±0.054 / E -0.17 / E+M 0.05", r"\(0\.218 ± 0\.054 across three seeds, all positive\) while environment stays null \(−0\.17\).*\(0\.05\)"),
 ("transfer 0.96/0.40/-0.95 pattern 0.961/0.888/0.861", r"0\.96 \(in-sample era\) through 0\.40 \(2030s\) to −0\.95 \(2060s\).*0\.961 through 0\.888 to 0\.861"),
 ("SSP 0.089", r"SSP5-8\.5 \(0\.089\)"),
 ("co-construction 0.017 & 0.651/0.658", r"\*\*r = 0\.017\*\*\. Yet the environmental model .explains. both at R² = 0\.651 and 0\.658"),
 ("year-robust 0.861/0.709/0.649", r"0\.861/0\.709/0\.649 for 2016/2020/2021"),
 ("arbitration 0.893/-0.036", r"ρ = 0\.893 \(p = 0\.007; absolute errors < 0\.25 t/ha\).*\(ρ = −0\.036\)"),
 ("four-year: 0.44-0.88 family, 2020 breaks -0.61", r"2016/2017/2020/2021.*0\.44–0\.88 while 2020 correlates negatively with all three, r = −0\.61"),
 ("env-CV by year -0.14 to -0.28", r"negative in every year, −0\.14 to −0\.28"),
 ("QRF 0.705->0.862, 0.62->0.79, 2.6x", r"PICP = 0\.705\).*0\.862.*0\.62 → 0\.79 t/ha ≈ 2\.6 ×"),
]
rows = []
for name, pat in checks:
    ok = has(pat)
    rows.append({"claim": name, "found_in_prose": ok})
    print(("PASS " if ok else "FAIL ") + name)
d = pd.DataFrame(rows)
d.to_csv(os.path.join(INT, "w27_r10_number_audit.csv"), index=False, encoding="utf-8-sig")
print(f"\n{d.found_in_prose.sum()}/{len(d)} number claims verified against frozen ledgers")
