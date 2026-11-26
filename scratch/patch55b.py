p = r'D:\2026-SP\src\s5_figures_main\w55_build_paper2_pdf.py'
s = open(p, encoding='utf-8').read()
old = '        words = text.split(" "); lo, hi, best = 4, len(words), None\n'
new = ('        words = text.split(" ")\n'
       '        if len(words) <= 4:\n'
       '            # short text: try whole, else new page (avoids empty binary-search range)\n'
       '            spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), text + " ",\n'
       '                                       fontname=font, fontsize=size, color=color,\n'
       '                                       lineheight=lead / size, align=align)\n'
       '            if spare < 0 and y > MT + 5:\n'
       '                new_page(); continue\n'
       '            if spare < 0:\n'
       '                return\n'
       '            y = MT + H - spare + after\n'
       '            return\n'
       '        lo, hi, best = 4, len(words), None\n')
assert old in s, "binary-search anchor missing"
s = s.replace(old, new)
# safety valve
s = s.replace('    cur = doc.new_page(width=A4[0], height=A4[1]); page_no += 1; y = MT',
              '    cur = doc.new_page(width=A4[0], height=A4[1]); page_no += 1; y = MT\n    if page_no > 80: raise RuntimeError("pagination runaway (>80 pages)")')
open(p, 'w', encoding='utf-8').write(s)
print("short-text branch + runaway guard added")
