# -*- coding: utf-8 -*-
"""W55: clean Agronomy-format PDF builder for Paper 2 (single column, A4,
Times-style body, figures embedded at first citation, captions below)."""
import os, re, glob
import fitz

ROOT = r"D:\2026-SP"
SRC = os.path.join(ROOT, "Paper", "Manuscript_v1.0_Prediction_Level_and_Pattern.md")
OUT = os.path.join(ROOT, "Paper", "Manuscript_v1.0_Prediction_Agronomy_format_v2.pdf")
FIGDIR = os.path.join(ROOT, "ManageFiles", "Submission_package_Paper2", "figures")

A4 = (595, 842); ML = MR = 54; MT, MB = 58, 64
W = A4[0] - ML - MR; H = A4[1] - MT - MB
BODY, BOLD, ITAL = "tiro", "tibo", "tiit"
SUB = {"\u2014": "-", "\u2013": "-", "\u2248": "~", "\u2192": "->", "\u2264": "<=", "\u2265": ">=",
       "\u2212": "-", "\u00b0": " deg", "\u03c1": "rho", "\u0394": "Delta"}

def sane(t):
    for k, v in SUB.items(): t = t.replace(k, v)
    return t

def clean(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return sane(t).strip()

doc = fitz.open(); page_no = 0; cur = None; y = MT
ALIGN_J = 3

def new_page():
    global cur, y, page_no
    cur = doc.new_page(width=A4[0], height=A4[1]); page_no += 1; y = MT
    if page_no > 80: raise RuntimeError("pagination runaway (>80 pages)")

def put(text, size, font, after=5, leading=None, align=None, indent=0, color=(0, 0, 0)):
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
            lo, hi, best = 1, len(words) - 1, 0
            while lo <= hi:         # largest prefix that fits: fill the page, flow the rest
                mid = (lo + hi) // 2
                if probe(" ".join(words[:mid])) >= 0: best = mid; lo = mid + 1
                else: hi = mid - 1
            if best == 0:           # not even one word fits -> go to a fresh page
                if y > MT + 5:
                    new_page(); continue
                best = 1
        chunk = " ".join(words[:best])
        spare = write(chunk)
        y = MT + H - spare + after
        text = " ".join(words[best:])
        if text:
            new_page()

def heading(t, size=11.5, after=7):
    global y
    if y + 55 > MT + H: new_page()      # keep the heading with its first lines
    put(t, size, BOLD, after=after, leading=size * 1.25, align=0)

def figure_block(n, caption):
    global cur, y
    g = glob.glob(os.path.join(FIGDIR, f"Figure{n}_*.png"))
    if not g: return
    pm = fitz.Pixmap(g[0]); aspect = pm.height / pm.width
    iw = W; ih = min(W * aspect, H * 0.56)
    cap_h = (int(len(caption) / 95) + 1) * 10.6 + 14
    if y + ih + cap_h + 8 > MT + H: new_page()
    x0 = ML + (W - iw) / 2
    cur.insert_image(fitz.Rect(x0, y, x0 + iw, y + ih), filename=g[0])
    y += ih + 6
    put(f"Figure {n}. " + caption, 8.5, BODY, after=10, leading=10.8, align=0)
    y += 2

# ---------------- booktabs three-line tables ----------------
NUMERIC = re.compile(r"^[-\u2013\u2014\d.,\s%+=<>n]*$")

def wrap_cell(text, width, size, font):
    words = text.split(); lines, cur_l = [], ""
    for w in words:
        t = (cur_l + " " + w).strip()
        if not cur_l or fitz.get_text_length(t, fontname=font, fontsize=size) <= width:
            cur_l = t
        else:
            lines.append(cur_l); cur_l = w
    if cur_l: lines.append(cur_l)
    return lines or [""]

def table_block(rows, caption=None):
    """Three-line (booktabs) table: heavy top/bottom rule, light rule under the
    header. Columns sized from content (word-level floor), wrapped, centred if
    numeric; the header repeats when the table breaks across pages. The caption
    is kept on the same page as the start of the table."""
    global cur, y
    size, lead, padx = 8.0, 9.7, 5.0
    ncol = len(rows[0])
    rows = [(r + [""] * (ncol - len(r)))[:ncol] for r in rows]
    def word_w(cells, font):
        return max((fitz.get_text_length(w, fontname=font, fontsize=size)
                    for t in cells for w in t.split()), default=0)
    nat, minw = [], []
    for c in range(ncol):
        col = [r[c] for r in rows]
        nat.append(max(fitz.get_text_length(rows[0][c], fontname=BOLD, fontsize=size),
                       max(fitz.get_text_length(t, fontname=BODY, fontsize=size) for t in col)) + 2 * padx)
        minw.append(max(word_w([rows[0][c]], BOLD), word_w(col, BODY)) + 2 * padx)
    if sum(nat) <= W:                      # expand to full text width
        widths = [n + (W - sum(nat)) * n / sum(nat) for n in nat]
    elif sum(minw) < W:                    # shrink, floor at longest word
        spare = W - sum(minw); shrink = [n - m for n, m in zip(nat, minw)]
        widths = [m + spare * s / max(sum(shrink), 1) for m, s in zip(minw, shrink)]
    else:
        widths = minw
    xs = [ML]
    for w in widths: xs.append(xs[-1] + w)
    aligns = [1 if all(NUMERIC.match(r[c]) for r in rows[1:]) else 0 for c in range(ncol)]

    def lines_of(r, font):
        return [wrap_cell(r[c], widths[c] - 2 * padx, size, font) for c in range(ncol)]

    def row_h(ls):
        return max(len(l) for l in ls) * lead + 5.5

    def rule(wt):
        cur.draw_line((ML, y), (ML + W, y), color=(0, 0, 0), width=wt)

    def row(ls, font, h):
        global y
        base0 = y + 3.0 + size * 0.75
        for c in range(ncol):
            for j, t in enumerate(ls[c]):
                tw = fitz.get_text_length(t, fontname=font, fontsize=size)
                x = xs[c] + (widths[c] - tw) / 2 if aligns[c] else xs[c] + padx
                cur.insert_text((x, base0 + j * lead), t, fontname=font, fontsize=size)
        y += h

    def head():
        global y
        hl = lines_of(rows[0], BOLD); hh = row_h(hl)
        rule(1.0); y += 4.2
        row(hl, BOLD, hh)
        y += 2.4; rule(0.5); y += 3.0

    hl = lines_of(rows[0], BOLD); hh = row_h(hl)
    body = [(lines_of(r, BODY)) for r in rows[1:]]
    hs = [row_h(ls) for ls in body]
    cap_h = (1 + len(caption) // 95) * 11.6 + 6 if caption else 0
    total = hh + sum(hs) + 18 + cap_h
    if y + total > MT + H and (total <= H or y + 70 + cap_h > MT + H):
        new_page()
    if caption:
        put(caption, 9.5, BOLD, after=5, align=0, leading=11.6)
    head()
    for ls, h in zip(body, hs):
        if y + h + 20 > MT + H:            # break: repeat header on the next page
            rule(0.5); y += 4
            new_page(); head()
        row(ls, BODY, h)
    y += 3.0; rule(1.0); y += 13

# ---------------- parse ----------------
md = open(SRC, encoding="utf-8").read()
body_md, tail_md = md.split("## Figure Captions")[0], md[md.find("## Figure Captions"):]
caps = {int(m.group(1)): clean(m.group(2)) for m in
        re.finditer(r"\*\*Figure (\d+)\.\*\* (.*?)(?=\n\n|\Z)", tail_md.split("## References")[0], flags=re.S)}
print("captions:", sorted(caps))

# ---------------- title block ----------------
new_page()
title = clean([l for l in body_md.split("\n") if l.startswith("# ")][0][2:])
put(title, 16, BOLD, after=10, leading=20, align=0)
abs_m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Keywords", body_md, flags=re.S).group(1)
kw_m = re.search(r"\*\*Keywords:\*\* (.*)", body_md).group(1)
put("Abstract: " + clean(abs_m), 9, BODY, after=6, leading=12.2, indent=18)
put("Keywords: " + clean(kw_m), 9, BODY, after=4, indent=18)
cur.draw_line((ML, y + 1), (ML + W, y + 1), color=(0.85, 0.85, 0.85), width=0.7); y += 8

# ---------------- body ----------------
placed = set()
lines = body_md.split("\n"); skip = True
SEP = re.compile(r"^[-: ]+$")

def read_table(src, j):
    """Collect consecutive markdown table rows from line list src at index j;
    skips blank lines before the first row."""
    rows = []
    while j < len(src):
        t = src[j].strip()
        if not t.startswith("|"):
            if not rows and not t:
                j += 1; continue
            break
        cells = [c.strip() for c in t.strip("|").split("|")]
        if not all(SEP.match(c) for c in cells):
            rows.append([clean(c) for c in cells])
        j += 1
    return rows, j

i = 0
while i < len(lines):
    s = lines[i].rstrip()
    if skip:
        if s.startswith("## 1."): skip = False
        else: i += 1; continue
    if not s.strip() or s.strip() == "---": i += 1; continue
    if s.startswith("**Table"):                 # caption: bind it to its table
        rows, j = read_table(lines, i + 1)
        if rows: table_block(rows, caption=clean(s))
        else: put(clean(s), 9.5, BOLD, after=5, align=0, leading=11.6)
    elif s.startswith("|"):
        rows, j = read_table(lines, i)
        table_block(rows)
    else:
        if s.startswith("### "): heading(clean(s[4:]), 10.5, after=5)
        elif s.startswith("## "): heading(clean(s[3:]))
        elif s.startswith("**Keywords"): i += 1; continue
        else: put(clean(s), 10, BODY, after=6, leading=13)
        j = i + 1
    for n in sorted(caps):
        if n in placed: continue
        if re.search(rf"Figure {n}\b", s):
            figure_block(n, caps[n]); placed.add(n)
    i = j
for n in sorted(caps):
    if n not in placed:
        figure_block(n, caps[n]); placed.add(n)

# ---------------- tables that sit after the figure captions ----------------
back_md = tail_md.split("## References")[0]
back_lines = back_md.split("\n")
i = 0
while i < len(back_lines):
    s = back_lines[i].rstrip()
    if s.startswith("**Table"):
        rows, j = read_table(back_lines, i + 1)
        if rows: table_block(rows, caption=clean(s))
        else: put(clean(s), 9.5, BOLD, after=5, align=0, leading=11.6)
        i = j; continue
    i += 1

# ---------------- references ----------------
refs = md[md.find("## References"):]
for s in refs.split("\n"):
    s = s.rstrip()
    if not s.strip() or s.strip() == "---": continue
    if s.startswith("## "):
        if y + 40 > MT + H: new_page()
        cur.draw_line((ML, y), (ML + W, y), color=(0.8, 0.8, 0.8), width=0.7); y += 7
        put(clean(s[3:]), 11, BOLD, after=7, align=0, leading=13)
    else:
        put(clean(s), 9.3, BODY, after=4, leading=11.8)

# ---------------- footers ----------------
total = len(doc)
for i, pg in enumerate(doc):
    pg.insert_text((ML, A4[1] - 30), "Agronomy 2026, 16, 0000", fontname=ITAL, fontsize=7.5, color=(0.35, 0.35, 0.35))
    pg.insert_text((ML + W - 40, A4[1] - 30), f"{i+1} of {total}", fontname=ITAL, fontsize=7.5, color=(0.35, 0.35, 0.35))
    pg.draw_line((ML, A4[1] - 36), (ML + W, A4[1] - 36), color=(0.85, 0.85, 0.85), width=0.5)

doc.save(OUT, deflate=True, garbage=3)
print("saved:", OUT, "| pages:", total, "| image pages:", sum(1 for p in doc if p.get_images()),
      "| MB:", round(os.path.getsize(OUT) / 1e6, 1))
