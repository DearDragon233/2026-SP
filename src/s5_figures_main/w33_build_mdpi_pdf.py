# -*- coding: utf-8 -*-
"""W33: Agronomy (MDPI) published-format PDF of Manuscript v5.0.
Single column (MDPI house style), A4, Times serif justified body, figures
embedded in the text at their first citation point, captions under figures,
MDPI-style footer (journal | volume | page of N)."""
import re, os, glob
import fitz

ROOT = r"D:\2026-SP"
SRC = os.path.join(ROOT, "Paper", "Manuscript_v5.0_fulltext.md")
OUT = os.path.join(ROOT, "Paper", "Manuscript_v5.0_MDPI_format.pdf")
FIGDIR = os.path.join(ROOT, "Outputs", "figures", "main")

A4 = (595, 842)
ML = MR = 54          # 1.9 cm side margins (MDPI)
MT, MB = 58, 64
W = A4[0] - ML - MR   # text width ~487pt (17.2 cm)
H = A4[1] - MT - MB
BODY, BOLDI = "tiro", "tibi"
BOLD, ITAL = "tibo", "tiit"

SUB = {"–": "-", "—": "-","\u2248": "~", "\u2192": "->", "\u2264": "<=", "\u2265": ">=", "\u2212": "-",
       "\u03c1": "rho", "\u03c3": "sigma", "\u0394": "Delta", "q\u0302": "q-hat",
       "\u2011": "-", "\u2211": "sum", "\u03c7\u00b2": "chi2", "\u2081": "1", "\u2082": "2"}

def sane(t):
    for k, v in SUB.items(): t = t.replace(k, v)
    return t

def clean(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return sane(t).strip()

doc = fitz.open()
page_no = 0
cur = None
y = MT
ALIGN_J = getattr(fitz, "TEXT_ALIGN_JUSTIFY", 3)

def new_page():
    global cur, y, page_no
    cur = doc.new_page(width=A4[0], height=A4[1])
    page_no += 1
    y = MT
    return cur

def put(text, size, font, after=5, leading=None, align=None, indent=0, right=0, color=(0,0,0)):
    """Write text with pagination; justify default for body."""
    global cur, y
    lead = leading or size * 1.28
    align = ALIGN_J if align is None else align
    text = sane(text)
    while text:
        rect = fitz.Rect(ML + indent, y, ML + W - right, MT + H)
        spare = cur.insert_textbox(rect, text, fontname=font, fontsize=size,
                                   color=color, lineheight=lead/size, align=align)
        if spare >= 0:
            y = MT + H - spare - 3 + after
            return
        words = text.split(" ")
        lo, hi, best = 8, len(words), None
        while lo <= hi:
            mid = (lo + hi)//2
            t = " ".join(words[:mid])
            if cur.insert_textbox(fitz.Rect(ML+indent, y, ML+W-right, MT+H), t+" ",
                                  fontname=font, fontsize=size, color=color,
                                  lineheight=lead/size, align=align) >= 0:
                best = mid; lo = mid+1
            else:
                hi = mid-1
        if best is None or best < 6:
            new_page(); continue
        t = " ".join(words[:best])
        cur.insert_textbox(fitz.Rect(ML+indent, y, ML+W-right, MT+H), t+" ",
                           fontname=font, fontsize=size, color=color,
                           lineheight=lead/size, align=align)
        text = " ".join(words[best:])
        new_page()

def heading(t, size=11.5, after=7):
    global cur, y
    if y + 30 > MT + H: new_page()
    put(t, size, BOLD, after=after, leading=size*1.25, align=0)

def figure_block(n, caption):
    """Float the figure to the next page top if it doesn't fit; then continue."""
    global cur, y
    g = glob.glob(os.path.join(FIGDIR, f"fig{n:02d}_*.png"))
    if not g: return
    pm = fitz.Pixmap(g[0])
    aspect = pm.height / pm.width
    iw = W
    ih = min(W * aspect, H * 0.56)
    # estimate caption height ~ (len(caption)/95 lines * 10.6)
    cap_h = max(1, int(len(caption)/95)+1) * 10.6 + 14
    if y + ih + cap_h + 8 > MT + H:
        new_page()
    x0 = ML + (W - iw)/2
    cur.insert_image(fitz.Rect(x0, y, x0+iw, y+ih), filename=g[0])
    y += ih + 6
    put(f"Figure {n}. " + caption, 8.5, BODY, after=10, leading=10.8, align=0)
    y += 2

# ---------------- parse source ----------------
md = open(SRC, encoding='utf-8').read()
body_md, tail_md = md.split("## Figure Captions")[0], md[md.find("## Figure Captions"):]
caps_raw = tail_md.split("## Table S1")[0]
caps = {}
for m in re.finditer(r"\*\*Fig (\d+)\*\* (.*?)(?=\n\n|\Z)", caps_raw, flags=re.S):
    caps[int(m.group(1))] = clean(m.group(2))
tail = tail_md[tail_md.find("## Table S1"):]

# ---------------- title block ----------------
new_page()
title = clean([l for l in body_md.split("\n") if l.startswith("# ")][0][2:])
put(title, 17, BOLD, after=10, leading=21, align=0)
put("by", 9, ITAL, after=3, align=0)
put("Yucheng Peng 1,*, [Co-author 2] 1, [Co-author 3] 1 and [Co-author 4] 1", 11, BODY, after=4, align=0)
put("1 College of Agronomy / National Maize Improvement Center, China Agricultural University, Beijing 100193, China",
    8.5, ITAL, after=3, align=0)
put("* Correspondence: [advisor email].", 8.5, BODY, after=8, align=0)

abs_m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Keywords", body_md, flags=re.S).group(1)
kw_m = re.search(r"\*\*Keywords:\*\* (.*)", body_md).group(1)
put("Abstract: " + clean(abs_m), 9, BODY, after=6, leading=12.2, indent=18, right=18)
put("Keywords: " + clean(kw_m), 9, BODY, after=4, indent=18, right=18)
cur.draw_line((ML, y+1, ), (ML+W, y+1), color=(0.85,0.85,0.85), width=0.7)
y += 8

# ---------------- body with in-text figures ----------------
placed = set()
lines = [l for l in body_md.split("\n")]
skip = True
for ln in lines:
    s = ln.rstrip()
    if skip:
        if s.startswith("## 1."): skip = False
        else: continue
    if not s.strip() or s.strip() == "---":
        continue
    if s.startswith("### "):
        heading(clean(s[4:]), 10.5, after=5)
    elif s.startswith("## "):
        heading(clean(s[3:]))
    elif s.startswith("**Keywords"):
        continue
    else:
        put(clean(s), 10, BODY, after=6, leading=13)
    # embed figures at first citation
    for n in sorted(caps):
        if n in placed: continue
        if re.search(rf"\bFig(?:ure)?\.?\s*{n}\b", s):
            figure_block(n, caps[n]); placed.add(n)
for n in sorted(caps):
    if n not in placed:
        figure_block(n, caps[n]); placed.add(n)

# ---------------- tail: Table S1, references, declarations ----------------
def render_tail(block):
    global y
    for s in block.split("\n"):
        s = s.rstrip()
        if not s.strip(): continue
        if s.startswith("## "):
            if y + 40 > MT + H: new_page()
            cur.draw_line((ML, y), (ML+W, y), color=(0.8,0.8,0.8), width=0.7); y += 7
            put(clean(s[3:]), 11, BOLD, after=7, align=0, leading=13)
        elif s.startswith("|"):
            cells = [clean(c) for c in s.strip("|").split("|")]
            if all(re.match(r"^[-: ]*$", c) for c in cells): continue
            put("   |   ".join(cells), 8.3, BODY, after=2.5, leading=10.2, align=0)
        elif s.startswith("**"):
            put(clean(s), 9.3, BOLD, after=3, align=0, leading=11.6)
        else:
            put(clean(s), 9.3, BODY, after=5, leading=11.8)

render_tail(tail)

# ---------------- MDPI-style footers (two-pass) ----------------
total = len(doc)
for i, pg in enumerate(doc):
    pg.insert_text((ML, A4[1]-30), f"Agronomy 2026, 16, 0000", fontname=ITAL, fontsize=7.5, color=(0.35,0.35,0.35))
    pg.insert_text((ML+W - 40, A4[1]-30), f"{i+1} of {total}", fontname=ITAL, fontsize=7.5, color=(0.35,0.35,0.35))
    pg.draw_line((ML, A4[1]-36), (ML+W, A4[1]-36), color=(0.85,0.85,0.85), width=0.5)

doc.save(OUT, deflate=True, garbage=3)
print("saved:", OUT, "| pages:", total, "| MB:", round(os.path.getsize(OUT)/1e6,1))
