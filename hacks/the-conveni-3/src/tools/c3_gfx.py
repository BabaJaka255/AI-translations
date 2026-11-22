"""Redraw Japanese text baked into textures (gfx/edits.json), for c3_build.

Each edit: {"pac": "ALLDATA"|"ONETEX", "member": n, "tim": k, "box": [x0, y0, x1, y1], "text": "...",
            "style": name from STYLES or an inline dict, "erase": "bg" | "col:X" | "none", "align": "left"|"center"}
The box is cleared (filled with the colour at "bgat", or each column copied from column X of the same rows),
the English is drawn to fit inside it (squeezed horizontally when too wide) and every pixel is mapped to the
nearest colour of the texture's own palette, so palettes and sizes never change.

  python3 c3_gfx.py preview <original.iso> <outdir>   PNGs of every edited texture, before/after side by side
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c3tex  # noqa: E402

FONTS = {
    "bold": "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
    "bolditalic": "/usr/share/fonts/opentype/inter/Inter-BoldItalic.otf",
    "semibold": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "sans": "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
}
STYLES = {
    # title menu items: yellow -> orange gradient, dark purple outline, italic
    "menu": {"ref": "Hg", "font": "bolditalic", "top": (255, 255, 120), "bottom": (255, 120, 0), "stroke": (40, 20, 60), "sw": 3},
    "menu_red": {"ref": "Hg", "font": "bolditalic", "top": (255, 90, 70), "bottom": (230, 20, 20), "stroke": (40, 20, 60), "sw": 3},
    "menu_cyan": {"ref": "Hg", "font": "bolditalic", "top": (120, 255, 255), "bottom": (40, 200, 120), "stroke": (150, 40, 170), "sw": 3},
    "opt": {"ref": "Hg", "font": "bold", "top": (110, 230, 255), "bottom": (60, 210, 140), "stroke": (20, 30, 80), "sw": 2},
    "button": {"ref": "HO", "font": "bold", "top": (255, 255, 255), "bottom": (220, 220, 220), "stroke": (20, 20, 20), "sw": 2},
    "card": {"ref": "Hg", "font": "bold", "top": (255, 40, 30), "bottom": (230, 10, 10), "stroke": (120, 0, 0), "sw": 1},
    "label": {"font": "bold", "top": (255, 255, 255), "bottom": (255, 255, 255), "stroke": None, "sw": 0},
    "stamp": {"font": "bold", "top": (255, 255, 255), "bottom": (240, 240, 240), "stroke": (30, 30, 30), "sw": 2},
    "help": {"ref": "Hg", "font": "bold", "top": (230, 255, 60), "bottom": (120, 230, 40), "stroke": (10, 40, 10), "sw": 2},
    "record": {"font": "bold", "top": (255, 250, 120), "bottom": (255, 160, 0), "stroke": (60, 30, 0), "sw": 2},
}
SS = 4  # supersampling


def render(text, w, h, st, align="left"):
    """RGBA image w x h with the text fitted inside (height-driven, squeezed when too wide)."""
    from PIL import Image, ImageDraw, ImageFont
    sw = st.get("sw", 0) * SS
    size = int(h * SS * st.get("scale", 1.0))
    font = ImageFont.truetype(FONTS[st["font"]], size)
    while True:
        ref = font.getbbox(st.get("ref", "Hgjy!"), stroke_width=sw)  # same size for every label of a given height
        th = ref[3] - ref[1]
        if th <= h * SS + SS or size < 8:
            bb = font.getbbox(text, stroke_width=sw)
            bb = (bb[0], ref[1], bb[2], ref[3])
            break
        size -= SS
        font = ImageFont.truetype(FONTS[st["font"]], size)
    tw = bb[2] - bb[0]
    big = Image.new("RGBA", (tw + 4 * SS, th + 4 * SS), (0, 0, 0, 0))
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).text((2 * SS - bb[0], 2 * SS - bb[1]), text, font=font, fill=255)
    if sw and st.get("stroke"):
        smask = Image.new("L", big.size, 0)
        ImageDraw.Draw(smask).text((2 * SS - bb[0], 2 * SS - bb[1]), text, font=font, fill=255, stroke_width=sw,
                                   stroke_fill=255)
        big.paste(Image.new("RGBA", big.size, tuple(st["stroke"]) + (255,)), (0, 0), smask)
    grad = Image.new("RGBA", big.size)
    top, bot = st["top"], st["bottom"]
    for y in range(big.size[1]):
        t = y / max(1, big.size[1] - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        ImageDraw.Draw(grad).line([(0, y), (big.size[0], y)], fill=c)
    big.paste(grad, (0, 0), mask)
    tw_px = max(1, round(big.size[0] / SS))
    th_px = max(1, round(big.size[1] / SS))
    if tw_px > w:
        tw_px = w
    small = big.resize((tw_px, min(h, th_px)), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = (w - small.size[0]) // 2 if align == "center" else 0
    out.alpha_composite(small, (x, (h - small.size[1]) // 2))
    return out


def tim_indices(d, base):
    """(indices as list of rows, width, height, palette RGBA list, writer) for a 4/8 bpp TIM."""
    t = c3tex.tim_parse(d, base)
    img = c3tex.tim_image(d, base)
    w, h = img.size
    pal = t["clut"]["colors"][: 1 << t["bpp"]]
    return img, t, pal


def tim_write(d: bytearray, t, img):
    px = img.tobytes()
    if t["bpp"] == 8:
        d[t["img_off"]:t["img_off"] + len(px)] = px
    else:
        out = bytearray(len(px) // 2)
        for i in range(0, len(px), 2):
            out[i >> 1] = (px[i] & 15) | ((px[i + 1] & 15) << 4)
        d[t["img_off"]:t["img_off"] + len(out)] = out


def nearest(pal, rgba, cache):
    k = rgba
    if k in cache:
        return cache[k]
    r, g, b, a = rgba
    best, bi = None, 0
    for i, (pr, pg, pb, pa) in enumerate(pal):
        if (pa > 0) != (a > 0):
            continue
        dist = (pr - r) ** 2 * 3 + (pg - g) ** 2 * 4 + (pb - b) ** 2 * 2
        if best is None or dist < best:
            best, bi = dist, i
    cache[k] = bi
    return bi


def apply_one(d: bytearray, base, edits):
    """Apply the edits for one TIM inside buffer d (TIM at offset base)."""
    from PIL import Image
    img, t, pal = tim_indices(d, base)
    idx = img.copy()
    orig = img.copy()
    rgba = img.convert("RGBA")
    W, H = img.size
    cache = {}
    for e in edits:
        st = STYLES[e["style"]] if isinstance(e["style"], str) else e["style"]
        x0, y0, x1, y1 = e["box"]
        er = e.get("erase", "bg")
        if er.startswith("col:"):
            cx = int(er[4:])
            for x in range(x0, x1):
                for y in range(y0, y1):
                    idx.putpixel((x, y), idx.getpixel((cx, y)))
        elif er.startswith("hgrad:"):  # horizontal gradient between the colours at (xa, ys) and (xb, ys)
            xa, xb, ys = (int(v) for v in er[6:].split(","))
            ca, cb = pal[orig.getpixel((xa, ys))], pal[orig.getpixel((xb, ys))]
            for x in range(x0, x1):
                f = min(1, max(0, (x - xa) / (xb - xa)))
                c = tuple(int(ca[i] + (cb[i] - ca[i]) * f) for i in range(3)) + (255,)
                v = nearest(pal, c, cache)
                for y in range(y0, y1):
                    idx.putpixel((x, y), v)
        elif er.startswith("vote:"):  # per pixel, the most common colour across N cells stacked every H rows
            H, N = (int(v) for v in er[5:].split(":"))
            from collections import Counter
            for x in range(x0, x1):
                for y in range(y0, y1):
                    c = Counter(orig.getpixel((x, y % H + k * H)) for k in range(N))
                    idx.putpixel((x, y), c.most_common(1)[0][0])
        elif er.startswith("row:"):  # each column filled from row Y (keeps a horizontal gradient)
            ry = int(er[4:])
            for x in range(x0, x1):
                v = idx.getpixel((x, ry))
                for y in range(y0, y1):
                    idx.putpixel((x, y), v)
        elif er.startswith("copy:"):  # copy a same-sized clean area (e.g. an emptied button) over the box
            sx, sy = (int(v) for v in er[5:].split(","))
            src = idx.crop((sx, sy, sx + x1 - x0, sy + y1 - y0))
            idx.paste(src, (x0, y0))
        elif er == "bg":
            bx, by = e.get("bgat", [W - 1, 0])
            v = idx.getpixel((bx, by))
            for x in range(x0, x1):
                for y in range(y0, y1):
                    idx.putpixel((x, y), v)
        if not e.get("text"):
            continue
        back = Image.new("RGBA", (x1 - x0, y1 - y0))
        for x in range(x0, x1):
            for y in range(y0, y1):
                back.putpixel((x - x0, y - y0), pal[idx.getpixel((x, y))])
        # "vbox": the whole label when it is split over two textures; box is the part in this one
        vx0, vy0, vx1, vy1 = e.get("vbox", e["box"])
        pad = e.get("pad", [0, 0])  # text area inset (x, y) inside the box
        vx0, vy0, vx1, vy1 = vx0 + pad[0], vy0 + pad[1], vx1 - pad[0], vy1 - pad[1]
        if e.get("rotate"):  # vertical label: drawn sideways, reading top to bottom
            full = render(e["text"], vy1 - vy0, vx1 - vx0, st, e.get("align", "left")).rotate(-90, expand=True)
        else:
            full = render(e["text"], vx1 - vx0, vy1 - vy0, st, e.get("align", "left"))
        txt = full.crop((x0 - vx0, y0 - vy0, x1 - vx0, y1 - vy0))  # areas outside the text box stay clear
        for x in range(x1 - x0):
            for y in range(y1 - y0):
                a = txt.getpixel((x, y))[3]
                if a < 40:
                    continue
                b = back.getpixel((x, y))
                c = txt.getpixel((x, y))
                f = a / 255
                mix = tuple(int(c[i] * f + b[i] * (1 - f)) for i in range(3)) + (255,)
                idx.putpixel((x0 + x, y0 + y), nearest(pal, mix, cache))
    tim_write(d, t, idx)
    _ = rgba
    return d


def load_edits(path=None):
    path = path or os.path.join(GAME, "gfx", "edits.json")
    return json.load(open(path, encoding="utf-8"))["edits"] if os.path.exists(path) else []


def group(edits):
    g = {}
    for e in edits:
        g.setdefault((e["pac"], e["member"], e["tim"]), []).append(e)
    return g


def apply_alldata(files, edits, lzs_decompress, lzs_compress):
    """files: ALLDATA members (list, changed in place). Returns {member: (old, new)} for checksum fixes."""
    changed = {}
    for (pac, m, k), es in sorted(group(edits).items()):
        if pac != "ALLDATA":
            continue
        old = changed[m][0] if m in changed else files[m]
        d = bytearray(lzs_decompress(files[m]) if files[m][:4] == b"LZS\0" else files[m])
        base = c3tex.tex_entries(d)[k][0]
        apply_one(d, base, es)
        files[m] = lzs_compress(bytes(d)) if old[:4] == b"LZS\0" else bytes(d)
        changed[m] = (old, files[m])
    return changed


def apply_onetex(members, edits):
    """ONETEX members are plain TIMs: edited in place, sizes unchanged. Returns {member: (old, new)}."""
    changed = {}
    for (pac, m, k), es in sorted(group(edits).items()):
        if pac != "ONETEX":
            continue
        d = bytearray(members[m])
        apply_one(d, 0, es)
        changed[m] = (members[m], bytes(d))
        members[m] = bytes(d)
    return changed


def preview(iso_path, out):
    from PIL import Image
    sys.path.insert(0, os.environ.get("RHTK", os.path.join(GAME, "toolkit")))
    from c3pac import lzs_compress, lzs_decompress, pac_read
    from rhtk import ps2
    os.makedirs(out, exist_ok=True)
    edits = load_edits()
    with ps2.Iso(iso_path) as iso:
        al = pac_read(iso.read_file("ALLDATA.PAC"))
        need_ot = any(e["pac"] == "ONETEX" for e in edits)
        ot = pac_read(iso.read_file("ONETEX.PAC")) if need_ot else []
    for (pac, m, k), es in sorted(group(edits).items()):
        if pac == "ALLDATA":
            d = bytearray(lzs_decompress(al[m]) if al[m][:4] == b"LZS\0" else al[m])
            base = c3tex.tex_entries(d)[k][0]
        else:
            d, base = bytearray(ot[m]), 0
        before = c3tex.tim_image(bytes(d), base).convert("RGBA")
        apply_one(d, base, es)
        after = c3tex.tim_image(bytes(d), base).convert("RGBA")
        W, H = before.size
        sheet = Image.new("RGBA", (W * 2 + 8, H), (255, 0, 255, 255))
        for i, im in enumerate((before, after)):
            bg = Image.new("RGBA", im.size, (255, 0, 255, 255))
            bg.alpha_composite(im)
            sheet.paste(bg, (i * (W + 8), 0))
        sheet.save(os.path.join(out, f"{pac}_{m:03d}_{k:02d}.png"))
        print(pac, m, k, len(es), "edits")
    _ = lzs_compress


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        preview(sys.argv[2], sys.argv[3])
