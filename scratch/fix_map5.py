p = r'D:\2026-SP\src\s5_figures_main\w57_study_area_map.py'
lines = open(p, encoding='utf-8').read().split('\n')
# locate the broken two-line statement
i = next(k for k, l in enumerate(lines) if l.strip().startswith('a.text(0.5, -0.26, "'))
assert lines[i+1].strip().startswith('.join(textwrap.wrap'), lines[i+1]
nl = chr(10)
fixed = [
 '    a.text(0.5, -0.26, nl.join(textwrap.wrap(u["n"], 30)), transform=a.transAxes,',
 '           ha="center", va="top", fontsize=6.0, color="#444444")',
]
lines[i:i+2] = fixed
src = '\n'.join(lines)
src = src.replace('    import textwrap\n', '    import textwrap\n    nl = chr(10)\n')
open(p, 'w', encoding='utf-8').write(src)
compile(src, p, 'exec')
print("line repaired; script compiles")
