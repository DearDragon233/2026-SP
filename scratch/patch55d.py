# -*- coding: utf-8 -*-
"""Replace put() in w55_build_paper2_pdf.py (lines 35..68) with a clean version.
Probing is always invisible (render_mode=3); exactly one visible write per chunk."""
p = r'D:\2026-SP\src\s5_figures_main\w55_build_paper2_pdf.py'
lines = open(p, encoding='utf-8').read().split('\n')
start = next(i for i, l in enumerate(lines) if l.startswith('def put('))
end = next(i for i, l in enumerate(lines) if l.startswith('def heading('))
new_put = r'''def put(text, size, font, after=5, leading=None, align=None, indent=0, color=(0, 0, 0)):
    """Paginated text. All layout probes are invisible; one visible write per chunk."""
    global cur, y
    lead = leading or size * 1.28
    align = ALIGN_J if align is None else align
    text = sane(text)
    R = lambda: fitz.Rect(ML + indent, y, ML + W, MT + H)
    def probe(t):
        return cur.insert_textbox(R(), t + " ", fontname=font, fontsize=size, color=color,
                                  lineheight=lead / size, align=align, render_mode=3)
    def write(t):
        return cur.insert_textbox(R(), t + " ", fontname=font, fontsize=size, color=color,
                                  lineheight=lead / size, align=align)
    guard = 0
    while text:
        guard += 1
        if guard > 400:
            raise RuntimeError("put(): pagination runaway for text starting: " + text[:40])
        words = text.split(" ")
        # how many words fit on the current page?
        if probe(text) >= 0:
            best = len(words)
        else:
            if y > MT + 5:          # not at page top -> start a new page and retry
                new_page(); continue
            lo, hi, best = 1, len(words) - 1, 0
            while lo <= hi:         # find the largest prefix that fits
                mid = (lo + hi) // 2
                if probe(" ".join(words[:mid])) >= 0: best = mid; lo = mid + 1
                else: hi = mid - 1
            if best == 0:           # a single word does not fit: force it (avoid loop)
                best = 1
        chunk = " ".join(words[:best])
        spare = write(chunk)
        y = MT + H - spare + after
        text = " ".join(words[best:])
        if text:
            new_page()
'''.split('\n')
lines[start:end] = new_put
open(p, 'w', encoding='utf-8').write('\n'.join(lines))
print(f"put() replaced (was lines {start+1}-{end}); new length {len(new_put)} lines")
