p = r'D:\2026-SP\scratch\w55_build_paper2_pdf.py'
lines = open(p, encoding='utf-8').read().split('\n')
lines[107] = 'caps_raw = tail_md.split("## References")[0]'
lines[109] = r'for m in re.finditer(r"\*\*(?:Fig|Figure) (\d+)\.?\*\* (.*?)(?=\n\n|\Z)", caps_raw, flags=re.S):'
open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print(lines[109])
