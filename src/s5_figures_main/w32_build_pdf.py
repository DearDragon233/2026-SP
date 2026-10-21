# -*- coding: utf-8 -*-
"""W32: build the complete PDF of Manuscript v5.0 with all figures embedded.
A4, Helvetica, title page -> abstract -> sections 1-11 -> figures (image +
caption per page) -> Table S1 -> references -> declarations."""
import re, os, glob
import fitz  # PyMuPDF

ROOT = r"D:\2026-SP"
SRC = os.path.join(ROOT, "Paper", "Manuscript_v5.0_fulltext.md")
OUT = os.path.join(ROOT, "Paper", "Manuscript_v5.0_with_figures.pdf")
FIGDIR = os.path.join(ROOT, "Outputs", "figures", "main")

A4 = (595, 842)
M = 52                      # margin
W, H = A4[0] - 2*M, A4[1] - 2*M
BODY, BOLD = "helv", "hebo"
ITAL = "heit"

doc = fitz.open()
page_no = 0

def new_page():
    global page_no
    p = doc.new_page(width=A4[0], height=A4[1])
    page_no += 1
    p.draw_text((M, H + M + 8), f"{page_no}", fontname=BODY, fontsize=8,
                color=(0.45, 0.45, 0.45)) if False else None
    p.insert_text((A4[0]/2, A4[1]-24), str(page_no), fontname=BODY, fontsize=8.5,
                  color=(0.4, 0.4, 0.4))
    return p

cur = new_page(); y = M

def need(h):
    global cur, y
    if y + h > H + M:
        cur = new_page(); y = M

def put(text, size, font, color=(0,0,0), leading=None, indent=0, space_after=6):
    global cur, y
    lead = leading or size * 1.32
    text = text.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    while text:
        rect = fitz.Rect(M + indent, y, M + W - indent*0.0, H + M)
        leftover = cur.insert_textbox(rect, text, fontname=font, fontsize=size,
                                      color=color, lineheight=lead/size, align=0)
        if leftover >= 0:
            y = H + M - leftover - 4
            y += space_after
            return
        # does not fit: put what fits by shrinking attempt -> simpler: fill page then continue
        # fitz wrote nothing; binary-search by words
        words = text.split(" ")
        lo, hi = 10, len(words)
        best = None
        while lo <= hi:
            mid = (lo + hi)//2
            t = " ".join(words[:mid])
            rect2 = fitz.Rect(M + indent, y, M + W, H + M)
            if cur.insert_textbox(rect2, t + " ", fontname=font, fontsize=size,
                                  color=color, lineheight=lead/size) >= 0:
                best = mid; lo = mid + 1
            else:
                hi = mid - 1
        if best is None or best < 5:
            cur = new_page(); y = M; continue
        t = " ".join(words[:best])
        rect2 = fitz.Rect(M + indent, y, M + W, H + M)
        cur.insert_textbox(rect2, t + " ", fontname=font, fontsize=size,
                           color=color, lineheight=lead/size)
        text = " ".join(words[best:])
        cur = new_page(); y = M

def clean(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    return t.strip()

def hr():
    global y
    need(10)
    cur.draw_line((M, y+2), (M+W, y+2), color=(0.75,0.75,0.75), width=0.6)
    y += 10

# ---------- parse markdown ----------
md = open(SRC, encoding="utf-8").read()
md = md.split("## Figure Captions")[0]  # main text first; captions used with figures
lines = md.split("\n")
i = 0
title_done = False
while i < len(lines):
    ln = lines[i].rstrip()
    if not ln.strip() or ln.strip() == "---":
        i += 1; continue
    if ln.startswith("# ") and not title_done:
        put(clean(ln[2:]), 17, BOLD, space_after=10); title_done = True
    elif ln.startswith("> "):
        t = clean(ln[2:])
        if t: put(t, 8.5, ITAL, color=(0.35,0.35,0.35), space_after=4)
    elif ln.startswith("### "):
        need(24); put(clean(ln[4:]), 11, BOLD, space_after=4)
    elif ln.startswith("## "):
        hr(); put(clean(ln[3:]), 12.5, BOLD, space_after=6)
    elif ln.startswith("|"):
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if all(re.match(r"^[-: ]+$", c) for c in cells):
            i += 1; continue
        put("   |   ".join(clean(c) for c in cells), 8.5, BODY, space_after=2)
    elif ln.startswith("**Keywords"):
        put(clean(ln), 9.5, ITAL, space_after=8)
    else:
        put(clean(ln), 10, BODY, space_after=7, leading=14.2)
    i += 1

# ---------- figures section ----------
cur = new_page(); y = M
put("Figures", 15, BOLD, space_after=10)
caps = {}
capsm = open(SRC, encoding="utf-8").read()
for m in re.finditer(r"\*\*Fig (\d+)\*\* (.*?)(?=\n\n|\Z)", capsm.split("## Figure Captions")[1] if "## Figure Captions" in capsm else "", flags=re.S):
    caps[int(m.group(1))] = m.group(2).strip()
figs = {}
for n in list(range(1, 18)):
    g = glob.glob(os.path.join(FIGDIR, f"fig{n:02d}_*.png"))
    if g: figs[n] = g[0]
ga = os.path.join(FIGDIR, "graphical_abstract.png")

def fig_page(img_path, title, caption):
    global cur, y
    cur = new_page(); y = M
    put(title, 11.5, BOLD, space_after=6)
    pix_w = W
    pm = fitz.Pixmap(img_path) if img_path.lower().endswith((".png")) else None
    aspect = pm.height / pm.width if pm else 0.66
    ih = min(pix_w * aspect, H * 0.62)
    rect = fitz.Rect(M, y, M + pix_w, y + ih)
    cur.insert_image(rect, filename=img_path)
    y += ih + 10
    put(clean(caption), 9, BODY, space_after=4, leading=12.5)

if os.path.exists(ga):
    fig_page(ga, "Graphical Abstract", "One environmental model, five targets: reported skill tracks target construction, not yield; the six-step pre-mapping audit protocol below turns each trap into a checkable pre-condition.")
for n in sorted(figs):
    fig_page(figs[n], f"Figure {n}. " + (caps.get(n, "").split(".")[0] if n in caps else ""), caps.get(n, os.path.basename(figs[n])))

# ---------- tail: Table S1 + refs + declarations ----------
cur = new_page(); y = M
tail_src = open(SRC, encoding="utf-8").read()
tail = tail_src[tail_src.find("## Table S1"):] if "## Table S1" in tail_src else ""
for ln in tail.split("\n"):
    s = ln.rstrip()
    if not s.strip(): continue
    if s.startswith("## "):
        hr(); put(clean(s[3:]), 12, BOLD, space_after=6)
    elif s.startswith("|"):
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.match(r"^[-: ]+$", c) for c in cells): continue
        put("   |   ".join(clean(c) for c in cells), 8.5, BODY, space_after=2)
    elif s.startswith("**"):
        put(clean(s), 9.5, BOLD, space_after=3)
    else:
        put(clean(s), 9.5, BODY, space_after=5, leading=13)

doc.save(OUT, deflate=True, garbage=3)
print("saved:", OUT, "| pages:", page_no, "| size MB:", round(os.path.getsize(OUT)/1e6, 1))
