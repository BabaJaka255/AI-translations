"""English fonts for The Conveni 3: single letters plus letter-pair glyphs.

Every character costs 2 bytes (Shift-JIS) and most text sits in fixed-size slots, so English would only
get half the room Japanese had. The renderer draws any 2-byte code from a per-font glyph table with its own
width (proportional), and adds a fixed gap (2 px in fonts 0-2) after each glyph. So a glyph that holds two
letters ("th", "e ", ...) drawn with that same 2 px gap between them looks exactly like the two letters,
and costs 2 bytes for 2 characters. No code change is needed: drawing, measuring and centring all just see
one wider glyph. ASCII ' ' is a 1-byte space (its width is patched in font_proof.SPACE_PX / here).

Fonts rebuilt: small (0), large (1), talk (2) in truefont.tex. The name-entry font (3) is left alone:
it keeps its kanji for the keyboard, and player names use its single letters.

Pages are rebuilt from scratch with: every non-kanji glyph the font had (kana, symbols, full-width Latin
and digits), KEEP_KANJI, the Latin letters the large font lacked (borrowed from the name font), then
as many pair glyphs as fit in the font with the least room. Pair codes are kanji codes from 0x889F up.

API:
  build(elf: bytearray, tf: bytearray, sn: bytes, pairs: list[str]) -> dict  (mapping, edits elf/tf in place)
  encode(text, mapping) -> bytes   (fewest bytes; control codes, %s and spaces stay ASCII)
  pair_ranking(corpus: str) -> list[str]   (pairs by bytes saved)
"""
import collections
import os
import re
import struct
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from c3font import FONTS, N, ELF_FOFF, ELF_VADDR, code_of, fw, idx, table, tex_tims  # noqa: E402
from c3tex import tim_parse  # noqa: E402

GAP = 2  # px the renderer adds after each glyph in fonts 0-2 (RAM 0x41F118, set at run time)
KEEP_KANJI = "円年月日時分秒万億店号"  # used by number/date formatting in code-built strings
FIRST_PAIR_CODE = 0x889F
LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,-'&:;()%+#*/\"~¥…=×\u2014"
CTRL = re.compile(r"/m(?:\([^)]*\))+|/k[A-Z]|/[A-Za-z][0-9]*|/[0-9]|%0?[0-9]*[sd]")  # /kA-/kV: wait codes take a letter


def _codes():
    for lead in list(range(0x88, 0xA0)) + list(range(0xE0, 0xEB)):
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            c = (lead << 8) | trail
            if c >= FIRST_PAIR_CODE and 0 <= idx(c) < N:
                yield c


def sjis(ch):
    """Shift-JIS code for one display character (ASCII goes full-width)."""
    ch = {"'": "’", '"': "”", "~": "～", "-": "‐", "¥": "￥", "\u2026": "…", "\u2014": "－"}.get(ch, ch)
    if " " < ch < "\x7f":
        ch = fw(ch)
    try:
        c = code_of(ch)
    except UnicodeEncodeError:
        return None
    return c if 0 <= idx(c) < N else None


class Page:
    def __init__(self, tf, tim_index):
        self.base = tex_tims(tf)[tim_index][0]
        p = tim_parse(tf, self.base)
        self.off, self.w, self.h = p["img_off"], 256, p["h"]
        self.colors = p["clut"]["colors"][:16]
        raw = tf[self.off:self.off + self.w * self.h // 2]
        self.px = bytearray(self.w * self.h)
        for i, b in enumerate(raw):
            self.px[2 * i], self.px[2 * i + 1] = b & 15, b >> 4

    def glyph(self, x, y, w, h):
        """Pixels as colour tuples (so glyphs can move between pages with different CLUT order)."""
        return [[self.colors[self.px[(y + r) * self.w + x + c]] for c in range(w)] for r in range(h)]

    def store(self, tf):
        tf[self.off:self.off + len(self.px) // 2] = bytes(
            self.px[i] | (self.px[i + 1] << 4) for i in range(0, len(self.px), 2))


def font_glyphs(elf, tf, sn, name):
    """{code: pixel rows} for every glyph the font has now; large also gets letters from the name font."""
    vt, tex, first, npages, h = FONTS[name]
    pages = [Page(tf, first + i) for i in range(npages)]
    out = {}
    for i, e in enumerate(table(elf, name)):
        if e[0] == 0xFF:
            continue
        code = i + 0x813F if i + 0x813F <= 0xE03F else i + 0xC190
        out[code] = pages[e[0]].glyph(e[1], e[2] * h, e[3], h)
    if name in ("large", "talk"):  # borrow missing Latin/punctuation from the 26 px name-entry font
        _, _, nfirst, nn, nh = FONTS["name"]
        npg = [Page(bytearray(sn), nfirst + i) for i in range(nn)]
        ntab = table(elf, "name")
        for ch in LATIN:
            c = sjis(ch)
            if c and c not in out and ntab[idx(c)][0] != 0xFF:
                e = ntab[idx(c)]
                if h <= nh:  # crop the middle rows
                    out[c] = npg[e[0]].glyph(e[1], e[2] * nh + (nh - h) // 2, e[3], h)
                else:  # pad top and bottom with background
                    g = npg[e[0]].glyph(e[1], e[2] * nh, e[3], nh)
                    bg = [g[0][0]] * e[3] if e[3] else []
                    top = (h - nh) // 2
                    out[c] = [list(bg)] * top + g + [list(bg)] * (h - nh - top)
                if name == "talk":  # talk font style: white fill, black outline, on its own key colour
                    out[c] = _talk_style(out[c], out)
    if name == "talk":  # smoother English: Latin letters, digits and punctuation redrawn from Inter
        out.update(_talk_latin(out))
    yen = code_of("￥")
    if name == "talk" and yen in out:  # full-width ￥ has wide blank margins: "with   ￥50,000" in event boxes
        g = out[yen]
        bg = g[0][0]
        cols = [x for x in range(len(g[0])) if any(r[x] != bg for r in g)]
        if cols:
            out[yen] = [r[max(0, cols[0] - 1):cols[-1] + 2] for r in g]
    _synth_quotes(out)
    return pages, out


TALK_TTF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Inter-ExtraBold.otf")
TALK_SIZE, TALK_BASE, SS = 22.5, 21, 4   # px size (caps ~17 px like the game's own), baseline row, supersampling
TALK_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,:;()&%+#*/-’”"


def _talk_latin(native):
    """Talk-font glyphs drawn from TALK_TTF in the game's own talk style: anti-aliased white fill, a 1 px black
    outline with a 2 px drop shadow down-right, on the talk font's key colour. The game's full-width Latin is
    blocky (the project lead, 2026-11-02: "choppy and rough"); widths come out about the same, so wrapping holds."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    ref = native.get(sjis("A")) or next(iter(native.values()))
    key, h = ref[0][0], len(ref)
    fnt = ImageFont.truetype(TALK_TTF, int(TALK_SIZE * SS))
    res = {}
    for ch in TALK_CHARS:
        c = sjis(ch) if ch not in "’”" else code_of(ch)
        if c is None:
            continue
        w = int(fnt.getlength(ch)) + 8 * SS
        big = Image.new("L", (w, h * SS), 0)
        ImageDraw.Draw(big).text((2 * SS, TALK_BASE * SS), ch, font=fnt, fill=255, anchor="ls")
        cov = big.resize((w // SS, h), Image.BOX)
        cw = cov.size[0]
        dil = cov.point(lambda v: 255 if v > 70 else 0).filter(ImageFilter.MaxFilter(3))
        blk = dil.copy()
        for d in (1, 2):
            sh = Image.new("L", cov.size, 0)
            sh.paste(dil, (d, d))
            blk.paste(255, mask=sh)
        cols = [x for x in range(cw) if any(blk.getpixel((x, y)) for y in range(h))]
        if not cols:
            continue
        rows = []
        for y in range(h):
            row = []
            for x in range(cols[0], cols[-1] + 1):
                v = cov.getpixel((x, y))
                row.append((v, v, v, 255) if v > 20 else (0, 0, 0, 255) if blk.getpixel((x, y)) else key)
            rows.append(row)
        res[c] = rows
    return res


def _talk_style(g, native):
    """Redraw a borrowed name-font glyph like the talk font's own: white fill with a 1 px black outline on the
    talk font's background (key) colour. (Inverting the name glyph gave a yellow background that the talk
    palette has no transparent match for, so ’ and , showed as solid bars in the tutorial.)"""
    ref = native.get(sjis("A")) or next(iter(native.values()))
    key, nb = ref[0][0], g[0][0]
    h, w = len(g), len(g[0]) + 2
    ink = [[False] * w for _ in range(h)]
    for y, line in enumerate(g):
        for x, p in enumerate(line):
            ink[y][x + 1] = max(abs(p[i] - nb[i]) for i in range(3)) > 60
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            if ink[y][x]:
                row.append((255, 255, 255, 255))
            elif any(ink[yy][xx] for yy in range(max(0, y - 1), min(h, y + 2))
                     for xx in range(max(0, x - 1), min(w, x + 2))):
                row.append((0, 0, 0, 255))
            else:
                row.append(key)
        out.append(row)
    return out


def _ink_rows(g, bg):
    return [y for y, line in enumerate(g) if any(abs(px[0] - bg[0]) > 60 for px in line)]


def _synth_quotes(out):
    """Fonts have no ’ or ”: make them from the comma, raised to the top of the capitals."""
    comma, cap = out.get(sjis(",")), out.get(sjis("A"))
    if not comma or not cap or not comma[0]:
        return
    bg = comma[0][0]
    ink, top = _ink_rows(comma, bg), _ink_rows(cap, bg)
    if not ink or not top:
        return
    w, h = len(comma[0]), len(comma)
    lo, hi = min(ink), max(ink)
    xs = [x for x in range(w) if any(abs(comma[y][x][0] - bg[0]) > 60 for y in ink)]
    x0, x1 = min(xs), max(xs) + 1
    mark = [comma[y][x0:x1] for y in range(lo, hi + 1)]
    apos = [[bg] * (x1 - x0) for _ in range(h)]
    for k, line in enumerate(mark):
        if min(top) + k < h:
            apos[min(top) + k] = list(line)
    if code_of("’") not in out:
        out[code_of("’")] = apos
    if code_of("”") not in out:
        out[code_of("”")] = [a + [bg] + b for a, b in zip(apos, apos)]
    dash = out.get(code_of("－"))
    if dash and code_of("‐") not in out:  # a short hyphen: the middle 7 px of the full-width dash
        cols = [x for x in range(len(dash[0])) if any(abs(r[x][0] - bg[0]) > 60 for r in dash)]
        if cols:
            mid = (min(cols) + max(cols)) // 2
            out[code_of("‐")] = [r[mid - 3:mid + 4] for r in dash]


def pair_ranking(corpus):
    """Character pairs worth a glyph, best first, by greedy left-to-right pairing of the corpus."""
    text = CTRL.sub("\0", corpus)
    cnt = collections.Counter()
    for word in re.split(r"[\0\n]", text):
        for i in range(len(word) - 1):
            a, b = word[i], word[i + 1]
            if a == " " and b == " ":
                continue
            # a pair with a space saves 1 byte (3 -> 2), two letters save 2 (4 -> 2)
            cnt[a + b] += 1 if " " in (a + b) else 2
    return [p for p, _ in cnt.most_common() if all(c == " " or sjis(c) for c in p)]


def build(elf, tf, sn, pairs, fonts=("small", "large", "talk"), max_pairs=None, pick=None):
    """Rebuild the three truefont fonts with kept glyphs + as many pairs as all fonts can hold.
    pick(p): optional code chooser (" " = the blank glyph); returns None to leave pair p out."""
    data = {f: font_glyphs(elf, tf, sn, f) for f in fonts}
    keep_k = {code_of(k) for k in KEEP_KANJI}
    kept = {f: {c: g for c, g in data[f][1].items() if c < 0x889F or c in keep_k} for f in fonts}
    codes = (c for c in _codes() if c not in keep_k)
    if pick is None:
        pick = lambda p: next(codes)  # noqa: E731
    mapping = {}
    glyph_sets = {f: dict(kept[f]) for f in fonts}
    space_w = {f: 6 for f in fonts}

    def pair_img(f, p):
        g = glyph_sets[f]
        parts = []
        for ch in p:
            if ch == " ":
                parts.append(None)
            else:
                c = sjis(ch)
                if c not in g:
                    return None
                parts.append(g[c])
        h = FONTS[f][4]
        bg = next(x for x in parts if x is not None)[0][0]
        rows = [[] for _ in range(h)]
        for k, part in enumerate(parts):
            if part is None:  # the space glyph's advance replaces this glyph's own width + gap
                for r in range(h):
                    rows[r] += [bg] * (space_w[f] - (GAP if k == 1 else 0))
                continue
            for r in range(h):
                rows[r] += part[r]
            if k == 0:
                for r in range(h):
                    rows[r] += [bg] * GAP
        return rows

    # capacity: pack kept glyphs first, then add pairs until some font is full
    packers = {f: _Packer(data[f][0], FONTS[f][4]) for f in fonts}
    placed = {f: {} for f in fonts}
    for f in fonts:
        for c, g in sorted(kept[f].items(), key=lambda kv: -len(kv[1][0])):
            placed[f][c] = packers[f].add(g)
            if placed[f][c] is None:
                raise RuntimeError(f"{f}: no room for kept glyph {c:04X}")
    # a blank glyph as wide as an ASCII space: the speech-box (talk) renderer drops ASCII ' ', so text drawn
    # there uses this code for a space that no pair glyph covers (encode(..., talk=True), mapping key " ")
    code = pick(" ")
    for f in fonts:
        bg = next(iter(kept[f].values()))[0][0]
        placed[f][code] = packers[f].add([[bg] * (space_w[f] - GAP) for _ in range(FONTS[f][4])])
    mapping[" "] = code
    for p in pairs:
        if max_pairs is not None and len(mapping) >= max_pairs:
            break
        imgs = {f: pair_img(f, p) for f in fonts}
        if any(v is None for v in imgs.values()):
            continue
        if not all(packers[f].fits(len(imgs[f][0])) for f in fonts):
            break
        code = pick(p)
        if code is None:
            continue
        for f in fonts:
            placed[f][code] = packers[f].add(imgs[f])
        mapping[p] = code
    # write pages and tables
    for f in fonts:
        packers[f].store(tf)
        o = FONTS[f][0] - ELF_VADDR + ELF_FOFF
        tab = bytearray(b"\xff\0\0\0" * N)
        for c, pos in placed[f].items():
            page, x, row, w = pos
            tab[4 * idx(c):4 * idx(c) + 4] = bytes((page, x, row, w))
        elf[o:o + 4 * N] = tab
    return {"pairs": mapping, "singles": sorted(set.intersection(*(set(kept[f]) for f in fonts)))}


class _Packer:
    """Row-based first fit over a font's pages (fixed page sizes, row height h)."""

    def __init__(self, pages, h):
        self.pages, self.h = pages, h
        for pg in pages:
            pg.px[:] = bytes(len(pg.px))  # index 0 = background in every font page
        self.rows = [(pi, r) for pi, pg in enumerate(pages) for r in range(pg.h // h)]
        self.free = [0] * len(self.rows)

    def fits(self, w):
        return any(f + w <= 256 for f in self.free)

    def add(self, g):
        w = len(g[0]) if g and g[0] else 0
        for k, f in enumerate(self.free):
            if f + w <= 256:
                pi, r = self.rows[k]
                pg = self.pages[pi]
                lut = {col: i for i, col in enumerate(pg.colors)}
                for y, line in enumerate(g):
                    base = (r * self.h + y) * pg.w + f
                    for x, col in enumerate(line):
                        pg.px[base + x] = lut.get(col, _nearest(pg.colors, col))
                self.free[k] = f + w
                return (pi, f, r, w)
        return None

    def store(self, tf):
        for pg in self.pages:
            pg.store(tf)


def _nearest(colors, col):
    return min(range(len(colors)), key=lambda i: sum((a - b) ** 2 for a, b in zip(colors[i], col)))


TALK = re.compile(r"/[rpk]|/s[0-9]|/f[0-9]")  # codes only speech-box (talk renderer) text uses


def is_talk(text):
    return bool(TALK.search(text))


def encode(text, mapping, talk=None):
    """Fewest-bytes encoding. mapping = build()["pairs"] ({"th": code}, " ": blank glyph).
    talk (default: guessed from the text's codes): the speech box drops ASCII spaces, so a space no pair
    covers is written as the blank glyph (2 bytes)."""
    pairs = mapping
    if talk is None:
        talk = is_talk(text)
    space = struct.pack(">H", pairs[" "]) if talk and " " in pairs else b" "
    toks = []  # (start, end, bytes)
    n = len(text)
    best = [None] * (n + 1)
    best[n] = (0, b"")
    for i in range(n - 1, -1, -1):
        opts = []
        m = CTRL.match(text, i)
        if m:
            opts.append((m.end(), m.group().encode("ascii")))
        else:
            ch = text[i]
            if ch == " ":
                opts.append((i + 1, space))
            else:
                c = sjis(ch)
                if c is None:
                    raise ValueError(f"no glyph for {ch!r} in {text!r}")
                opts.append((i + 1, struct.pack(">H", c)))
            if i + 1 < n and len(text[i:i + 2]) == 2 and text[i:i + 2] in pairs:
                opts.append((i + 2, struct.pack(">H", pairs[text[i:i + 2]])))
        cands = [(len(b) + best[j][0], j, b) for j, b in opts if best[j] is not None]
        cost, j, b = min(cands, key=lambda t: (t[0], -t[1]))
        best[i] = (cost, b + best[j][1])
    return best[0][1]
