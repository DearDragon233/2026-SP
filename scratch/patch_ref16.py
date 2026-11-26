p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
# cite the benchmark paper where the design rationale is stated (intro, on blocked validation + baselines)
old = "And a training-mean predictor is a necessary baseline for small county-year panels, because flexible estimators can fit noise when the number of independent weather series is low [12,13]."
assert old in s
s = s.replace(old, old + " Calls for standardised benchmark practice in crop prediction make the same point: fixed cohorts, declared baselines and validation splits released with the results [16].")
# add entry 16 after entry 15
anchor = "15. Gao, J.; Liao, J.; Liu, Y."
i = s.find(anchor); assert i > 0
j = s.find("\n", i)
entry16 = ("\n16. Yan, M.; Wang, W.; Zhang, Y.; et al. Standardizing benchmarks for plant genomic prediction. "
           "*Agronomy* 2026, 16, 1131. DOI: 10.3390/agronomy16121131.")
s = s[:j] + entry16 + s[j:]
open(p, 'w', encoding='utf-8').write(s)

import re
body, refs = s.split("## References")
cited = set()
for m in re.finditer(r"\[(\d+)(?:[–-](\d+))?\]", body):
    a = int(m.group(1)); b = m.group(2)
    cited.update(range(a, int(b) + 1) if b else [a])
entries = [int(x) for x in re.findall(r"^(\d+)\. ", refs, flags=re.M)]
print("entries:", entries, "| cited:", sorted(cited))
print("missing:", sorted(cited - set(entries)), "| uncited:", sorted(set(entries) - cited))
