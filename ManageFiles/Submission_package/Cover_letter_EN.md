# Cover Letter（致 Agronomy 编辑）

Dear Editors of Agronomy (Section: Precision and Digital Agriculture),

We are pleased to submit our manuscript "The Trap of Model-Derived Yield Targets: A Controlled Diagnostic of Target Construction, Validation Design, and Co-Construction Bias in County-Scale Yield Mapping" for consideration as a research article.

Regional yield mapping increasingly trains machine-learning models against model-derived targets because grid-scale field measurements are rare. Our manuscript asks what such targets do to reported skill, and answers with a controlled diagnostic built entirely on public data: (i) a circular-validation upper bound (interpolated target R2 = 0.98 versus a leave-one-out interpolation bound of 0.20-0.27); (ii) the mechanism by which checkerboard cross-validation becomes structurally inert in small domains (between-block distance pinned at 2.3-2.4 km across all block sizes), with gradient-cutting schemes as the honest alternative; (iii) a detectability framework reconciling county-scale nulls with genuine regional signal (R2 = 0.69 across 7,784 grids) via window sweeps and planted-signal power analysis; and (iv) directional proof of co-construction bias - two national products correlate at r = 0.017 while one environmental model "explains" both at R2 near 0.65, and official provincial statistics arbitrate which product carries real signal (rho = 0.893 versus -0.04).

The work culminates in a six-step pre-mapping audit protocol in which every step costs minutes and requires no new data. We believe this agenda closely matches the journal's recent methodological direction, including the 2026 perspective on standardizing benchmarks for plant genomic prediction (Agronomy 16, 1131): our manuscript delivers that benchmarking spirit on the yield-mapping side.

All data are public with file-level checksums; code, fold assignments, seeds, and every statistical ledger are frozen in the repository, and each number in the manuscript regenerates from a scripted ledger (27/27 claims verified programmatically). The manuscript is not under consideration elsewhere; all authors have approved the submission and declare no conflicts of interest.

Suggested reviewers (no collaborations or conflicts in the past five years): Edzer Pebesma (University of Münster; spatial validation), Pierre Ploton (IRD; spatial model assessment), Alexandre Wadoux (University of Sydney; map accuracy evaluation), and a senior author of the ChinaWheatYield30m dataset for the remote-sensing perspective.

Thank you for your consideration.

Yucheng Peng, on behalf of all authors
College of Agronomy / National Maize Improvement Center, China Agricultural University
