p = r'D:\2026-SP\src\s5_figures_main\w55_build_paper2_pdf.py'
s = open(p, encoding='utf-8').read()
# make every PROBE write invisible (render_mode=3), final write visible
s = s.replace(
 'spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), t + " ",\n'
 '                                       fontname=font, fontsize=size, color=color,\n'
 '                                       lineheight=lead / size, align=align)\n'
 '            if spare < 0 and y > MT + 5:',
 'spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), t + " ",\n'
 '                                       fontname=font, fontsize=size, color=color,\n'
 '                                       lineheight=lead / size, align=align, render_mode=3)\n'
 '            if spare >= 0:  # fits: write for real\n'
 '                spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), text + " ",\n'
 '                                           fontname=font, fontsize=size, color=color,\n'
 '                                           lineheight=lead / size, align=align)\n'
 '            if spare < 0 and y > MT + 5:')
s = s.replace(
 '            spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), text + " ",\n'
 '                                       fontname=font, fontsize=size, color=color,\n'
 '                                       lineheight=lead / size, align=align)\n'
 '            if spare < 0:\n'
 '                return',
 '            spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), text + " ",\n'
 '                                       fontname=font, fontsize=size, color=color,\n'
 '                                       lineheight=lead / size, align=align, render_mode=3)\n'
 '            if spare < 0:\n'
 '                return')
# the binary-search probe
old_bs = ('            spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), t + " ",\n'
          '                                       fontname=font, fontsize=size, color=color, lineheight=lead / size, align=align)\n'
          '            if spare >= 0: best = mid; lo = mid + 1')
new_bs = ('            spare = cur.insert_textbox(fitz.Rect(ML + indent, y, ML + W, MT + H), t + " ",\n'
          '                                       fontname=font, fontsize=size, color=color, lineheight=lead / size, align=align, render_mode=3)\n'
          '            if spare >= 0: best = mid; lo = mid + 1')
assert old_bs in s, "binary-search probe anchor missing"
s = s.replace(old_bs, new_bs)
open(p, 'w', encoding='utf-8').write(s)
print("probes made invisible; final writes visible")
