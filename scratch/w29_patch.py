# -*- coding: utf-8 -*-
"""W29 R2-R5: references, abstract, declarations, captions, limitations."""
import re
p = r'D:\2026-SP\Paper\Manuscript_v5.0_fulltext.md'
s = open(p, encoding='utf-8').read()

new_abs = ("Regional yield mapping relies on model-derived targets because grid-scale field measurements are rare. "
"We audited what such targets do to the apparent skill of environmental machine learning in Pinggu, Beijing "
"(234 grids, 0.0417 degrees, 24 variables), where a provenance audit showed that all four obtainable yield "
"targets are model products: a process-model baseline (43 grids, 7.21 plus or minus 0.23 t/ha), its "
"interpolation, a Bayesian blend, and a satellite retrieval. The interpolated target yields cross-validated "
"R2 = 0.98 although leave-one-out interpolation of its own sources reaches only 0.20 to 0.27, bounding "
"circular validation. Checkerboard cross-validation is structurally inert in a domain 5.6 variogram ranges "
"wide (between-block distance pinned at 2.3 to 2.4 km; optimism gap from +0.113 to -0.006), whereas "
"gradient-cutting schemes reveal gaps up to +0.54. The same framework recovers R2 = 0.690 on a 7,784-grid "
"regional gradient yet detects nothing at n = 43 even for planted true signals of R2 = 0.5: county-scale "
"nulls are detectability limits. Two national products correlate at r = 0.017 while one environmental model "
"explains both at R2 near 0.65; provincial statistics arbitrate (rho = 0.893 vs -0.04), proving "
"co-construction bias. We release a six-step pre-mapping audit protocol that turns each trap into a "
"checkable pre-condition.")
s = re.sub(r'## Abstract\n\n.*?\n\n\*\*Keywords', '## Abstract\n\n' + new_abs + '\n\n**Keywords', s, flags=re.S)

s = s.replace('24 modelling variables from WorldClim 2.1 (19 bioclimatic plus monthly temperature and precipitation aggregates), SoilGrids 2.0 topsoil properties, and SRTM terrain derivatives',
 '24 modelling variables from WorldClim 2.1 [13] (19 bioclimatic plus monthly temperature and precipitation aggregates), SoilGrids 2.0 topsoil properties [14], and SRTM terrain derivatives')

s = s.replace('None of these caveats touches the protocol, whose steps consume only pre-modelling information.',
 'None of these caveats touches the protocol, whose steps consume only pre-modelling information. A final boundary is geographic and crop-system scope: every empirical result here comes from Chinese winter-wheat systems, and the protocol itself, while domain-agnostic by construction, has yet to be exercised on other crops and continents; we encourage such transfer tests and release all tooling to enable them.')

captions_file = r'D:\2026-SP\scratch\w29_captions.txt'
refs_file = r'D:\2026-SP\scratch\w29_refs.txt'

s = s.replace('*(Figs 2–3, 5–13 as per repository figure plan; captions to be finalised with figure production.)*',
              open(captions_file, encoding='utf-8').read().strip())
s = s.rstrip() + '\n\n' + open(refs_file, encoding='utf-8').read().strip() + '\n'
open(p, 'w', encoding='utf-8').write(s)
aw = len(re.search(r'## Abstract\n\n(.*?)\n\n\*\*Keywords', s, re.S).group(1).split())
print('abstract words:', aw)
print('refs section:', '## References' in s, '| declarations:', '## Declarations' in s)
print('caption TODO left:', 'to be finalised' in s)
