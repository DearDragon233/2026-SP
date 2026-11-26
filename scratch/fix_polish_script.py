p = r'D:\2026-SP\scratch\w56_polish.py'
s = open(p, encoding='utf-8').read()
# (4) remove no-op replacement
noop = ('rep("Re-centring the predictions to the observed level turned the 540.2 kg/ha advantage into a 145.3 kg/ha deficit (Figure 3).",\n'
        '    "Re-centring the predictions to the observed level turned the 540.2 kg/ha advantage into a 145.3 kg/ha deficit (Figure 3).")\n')
assert noop in s; s = s.replace(noop, '')
noop2 = ('rep("| Raw positive, de-levelled positive | 2 | Forward-year random forest, statistics (+61.1 to +7.7); Zhoukou random forest, satellite (+746.0 to +1.8) |",\n'
         '    "| Raw positive, de-levelled positive | 2 | Forward-year random forest, statistics (+61.1 to +7.7); Zhoukou random forest, satellite (+746.0 to +1.8) |")\n')
assert noop2 in s; s = s.replace(noop2, '')
# (2) bootstrap interval: use ledger values 0.428-0.999
s = s.replace("(permutation p = 0.017; bootstrap 95% interval 0.43 to 1.00)", "(permutation p = 0.017; bootstrap 95% interval 0.43 to 0.999)")
s = s.replace("a bootstrap interval of 0.43 to 1.00 and a single model arm", "a bootstrap interval of 0.43 to 0.999 and a single model arm")
# (3) drop the unsupported claim in 4.4
old = " The step that makes a county-scale transfer test interpretable is thus the decomposition of the metric. Changing the target or the estimator alone would not have exposed it.\")"
assert old in s
s = s.replace(old, " Level-and-pattern decomposition is therefore the step that makes a county-scale transfer test interpretable.\")")
open(p, 'w', encoding='utf-8').write(s)
print("polish script corrected")
