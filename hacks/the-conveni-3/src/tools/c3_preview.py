"""Preview English text in the game's own fonts and boxes, without running the game.

  python3 tools/c3_preview.py <built.iso> [out_dir]      (default out_dir: preview/)

Draws every string of each box type with the real glyphs from the built ISO (talk font for speech bubbles,
small font for panels), wraps it the way the game does (letter by letter once a line passes the box's width,
which is what splits words like "rec/over"), and paginates it. Each box is outlined:
  green  = fits;  orange = the game will re-wrap a line (word split);  red = more lines than the box holds,
  so the game scrolls or opens a second bubble on its own.
Box widths/line counts are the ones measured in game (notes/rom.md). One PNG sheet per box type, plus index.html.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get("RHTK", os.path.join(GAME, "toolkit")))
from PIL import Image, ImageDraw  # noqa: E402

import c3_glyphs as G  # noqa: E402
import c3_tr as T  # noqa: E402
from c3font import idx, table  # noqa: E402
from c3pac import lzs_decompress, pac_read  # noqa: E402
from rhtk import ps2  # noqa: E402

GAP, SPACE = 2, 6
CODES = re.compile(r"/[rn]|/m(?:\([^)]*\))+|/k[A-Z]|/w[0-9]+|/s[0-9]+|/f[0-9]+|/i[0-9]+|/c[0-9]|/g[0-9]|/[A-Za-z][0-9]*|/[0-9]")


def load_fonts(iso):
    with ps2.Iso(iso) as i:
        elf = bytearray(i.read_file("SLPM_623.22"))
        al = pac_read(i.read_file("ALLDATA.PAC"))
    tf, sn = bytearray(lzs_decompress(al[51])), lzs_decompress(al[25])
    fonts = {}
    for name in ("talk", "small"):
        _, out = G.font_glyphs(elf, tf, sn, name)
        tab, nt = table(elf, name), table(elf, "name")

        def wf(code, tab=tab, nt=nt, name=name):
            e = tab[idx(code)] if 0 <= idx(code) < len(tab) else (0xFF,)
            if e[0] == 0xFF and name == "talk" and 0 <= idx(code) < len(nt):
                e = nt[idx(code)]
            return e[3] if e[0] != 0xFF else 18
        fonts[name] = (out, wf)
    return fonts


class Font:
    def __init__(self, glyphs, key, wfun=None):
        self.g, self.key, self.wfun = glyphs, key, wfun
        self.h = len(next(iter(glyphs.values())))

    def glyph(self, ch):
        c = G.sjis(ch)
        return self.g.get(c) if c else None

    def width(self, ch):
        if self.wfun:  # same measure as the wrap tools (c3_tr._width), from the built ELF's width table
            return T._width(ch, self.wfun)
        if ch == " ":
            return SPACE
        g = self.glyph(ch)
        return (len(g[0]) if g else 18) + GAP

    def draw(self, img, x, y, ch, tint=None):
        g = self.glyph(ch)
        if not g:
            return
        for r, row in enumerate(g):
            for c, px in enumerate(row):
                px = tuple(px[:3])
                if px != self.key and len(px) == 3 and not (self.key is None and px == row[0]):
                    img.putpixel((x + c, y + r), px if not tint else tint)


def layout(text, font, limit):
    """Lines as the game draws them: explicit breaks kept, letter-wrap past `limit` px. Returns (lines, rewrapped)."""
    out, rewrapped = [], False
    for seg in re.split(r"/r|/n", text):
        cur, w = "", 0
        for ch in seg:
            cw = font.width(ch)
            if cur and w + cw > limit:
                out.append(cur)
                rewrapped = True
                cur, w = ("", 0) if ch == " " else (ch, cw)
                continue
            cur += ch
            w += cw
        out.append(cur)
    return out, rewrapped


def wordwrap(text, font, limit):
    """Break at spaces the way the Fixture details panel does since tools/c3_wordwrap.py."""
    lines, cur = [], ""
    for wd in text.split(" "):
        trial = f"{cur} {wd}" if cur else wd
        if cur and sum(font.width(c) for c in trial) > limit:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    return "/n".join(lines + [cur])


def pages_of(text, keep_boxes=False):
    """Split on page ends (/p); drop other control codes but keep line breaks."""
    pages = []
    for pg in re.split(r"/p|(?=/m\()", text):
        boxes = re.findall(r"/m\([^)]*\)\(([-0-9]+),([-0-9]+),([-0-9]+),([0-9]+),([0-9]+)\)", pg)
        clean = CODES.sub(lambda m: m.group() if m.group() in ("/r", "/n") else "", pg)
        clean = clean.replace("~", "～")
        if clean.strip() or (keep_boxes and boxes):  # a box-only page still sets the next bubble's size
            pages.append((clean.strip(), boxes[-1] if boxes else None))
    return pages


def render_box(font, title, text, limit, lines_max, scale=1):
    lines, rewrapped = layout(text, font, limit)
    while lines and not lines[-1]:
        lines.pop()
    lh = font.h + 4
    W, H = limit + 20, max(lines_max, len(lines)) * lh + 34
    img = Image.new("RGB", (W, H), (236, 232, 220) if font.key != (0, 0, 255) else (25, 35, 95))
    d = ImageDraw.Draw(img)
    over = len(lines) > lines_max
    col = (200, 30, 30) if over else (230, 140, 0) if rewrapped else (40, 150, 60)
    d.rectangle([0, 0, W - 1, H - 1], outline=col, width=3)
    d.text((6, 4), title, fill=(60, 60, 60) if font.key != (0, 0, 255) else (200, 200, 220))
    d.line([(10 + limit, 18), (10 + limit, H - 6)], fill=(170, 170, 200))
    if lines_max < len(lines):
        y = 20 + lines_max * lh
        d.line([(4, y), (W - 4, y)], fill=(200, 30, 30), width=2)
    for i, ln in enumerate(lines):
        x = 10
        for ch in ln:
            font.draw(img, x, 20 + i * lh, ch)
            x += font.width(ch)
    status = "scrolls" if over else "re-wraps" if rewrapped else "ok"
    return img, status


def sheet(boxes, cols=3):
    if not boxes:
        return None
    cw = max(b.width for b in boxes) + 10
    rows, y, heights = [], 0, []
    for i in range(0, len(boxes), cols):
        heights.append(max(b.height for b in boxes[i:i + cols]) + 10)
    img = Image.new("RGB", (cw * cols, sum(heights)), (90, 110, 100))
    y = 0
    for r, h in enumerate(heights):
        for c, b in enumerate(boxes[r * cols:(r + 1) * cols]):
            img.paste(b, (c * cw + 5, y + 5))
        y += h
    return img


def main():
    iso = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(GAME, "preview")
    os.makedirs(out, exist_ok=True)
    fonts = load_fonts(iso)
    talk = Font(fonts["talk"][0], (255, 79, 255), fonts["talk"][1])
    small = Font(fonts["small"][0], (0, 0, 255), fonts["small"][1])
    elf = {e["id"]: e for e in json.load(open(os.path.join(GAME, "script", "elf.json"), encoding="utf-8"))["entries"]}
    cn3 = {e["id"]: e for e in json.load(open(os.path.join(GAME, "script", "cn3.json"), encoding="utf-8"))["entries"]}
    groups = {}

    def add(group, font, title, text, limit, lines):
        img, st = render_box(font, title, text, limit, lines)
        groups.setdefault(group, []).append((img, st, title))

    # tutorials: each page in its own /m bubble (text width ~ box width - 65, observed), 335 before the first /m
    for tid in (787, 788):
        limit, nlines = 335, 4
        for k, (pg, box) in enumerate(pages_of(elf[tid]["en"], keep_boxes=True)):
            if box:
                limit, nlines = int(box[3]) - 65, int(box[4])
            if not pg:
                continue
            add("tutorial", talk, f"#{tid} p{k + 1}", pg, limit, nlines)
    # help bubble (triangle): commands help and the angel's event advice, ~351 px, 4 lines
    for i in range(743, 783):
        if elf.get(i, {}).get("en"):
            add("help", talk, f"elf #{i}", pages_of(elf[i]["en"])[0][0] if pages_of(elf[i]["en"]) else "", 351, 4)
    for line in open(os.path.join(GAME, "script", "tr", "cn3_angel.tsv"), encoding="utf-8"):
        if line[:1].isdigit():
            i = int(line.split("\t")[0])
            add("advice", talk, f"cn3 #{i}", pages_of(cn3[i]["en"])[0][0], 351, 4)
    # Conveni Encyclopedia answers: tall box, ~390 px, 7 lines
    for i, e in sorted(elf.items()):
        o = int(e["offset"], 16)
        if 0x42E000 <= o < 0x431000 and e["jp"].count("/n") >= 2 and e["en"]:
            add("encyclopedia", talk, f"elf #{i}", pages_of(e["en"])[0][0], 390, 7)
    # Let's Play! scenario goals: small bubble on the scenario list, ~240 px, 4 lines
    for i in (357, 358, 359, 361, 363):
        add("scenario_goals", talk, f"elf #{i}", elf[i]["en"], 235, 4)
    # Fixture details panel: small font; description 2 lines, broken between words since tools/c3_wordwrap.py
    # (lines end at ~232 px, measured in game: 225 < limit <= 238); long name 1 line, ~250 px
    for i, e in sorted(cn3.items()):
        if any(w[0] == 26 for w in e["where"]) and e["en"]:
            if e.get("field") == 64:
                add("fixture_desc", small, f"cn3 #{i}", wordwrap(e["en"], small, 232), 232, 2)
                # same text in the one-line bar under Edit Interior
                add("fixture_bar", small, f"cn3 #{i}", e["en"], 440, 1)
            elif e.get("field") == 32:
                add("fixture_names", small, f"cn3 #{i}", e["en"], 250, 1)

    rows = []
    for g, items in groups.items():
        bad = [t for _, st, t in items if st != "ok"]
        img = sheet([b for b, _, _ in items])
        img.save(os.path.join(out, f"{g}.png"))
        rows.append(f"<h2>{g} ({len(items)} boxes, {len(bad)} flagged)</h2>"
                     f"<p>{html.escape(', '.join(bad)) or 'all fit'}</p><img src='{g}.png'>")
        print(f"{g}: {len(items)} boxes, {len(bad)} flagged {bad[:12]}")
    open(os.path.join(out, "index.html"), "w").write(
        "<!doctype html><meta charset=utf-8><title>Conveni 3 text preview</title>"
        "<body style='background:#333;color:#eee;font-family:sans-serif'>"
        "<p>Green: fits. Orange: the game re-wraps a line. Red: too many lines (scrolls / second bubble).</p>"
        + "".join(rows))


if __name__ == "__main__":
    main()
