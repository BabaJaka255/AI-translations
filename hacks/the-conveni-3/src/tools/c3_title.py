"""Title screen subtitle: "～あの町を独占せよ～" -> "~Corner the Market!~".

The title picture is ALLDATA member 43 (title_eb.tex): six 32-bit TIMs (flag 3; RGBA, alpha 0-128) that tile a
640x512 screen as 256+256+128 wide by 2 rows. The subtitle sits at about x 376-532, y 208-230, right of the
big "3". The Japanese logo itself ("ザ・コンビニ 3") is the game's brand mark and stays.

  apply(files, lzs_decompress, lzs_compress) -> (old, new) or None   used by c3_build (then fix_sum)
  python3 c3_title.py <original.iso> <out.png>                       preview
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3tex  # noqa: E402

MEMBER = 43
EB_MEMBER, EB_TEX, EB_LEN = 42, 0x1AC, 0x18   # title_eb.eb: tex offset word at 0x14 (= EB_TEX), length at 0x18
TILES = [(0, 0), (256, 0), (512, 0), (0, 256), (256, 256), (512, 256)]
TEXT = "~Corner the Market!~"
BOX = (377, 207, 536, 231)       # erased area [x0, y0, x1, y1)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBoldItalic.otf"
SIZE = 15


def _tiles(d):
    for k, (b, _) in enumerate(c3tex.tex_entries(d)):
        bn, fx, fy, w, h = struct.unpack_from("<IHHHH", d, b + 8)
        assert struct.unpack_from("<I", d, b + 4)[0] & 7 == 3, "not a 32-bit TIM"
        yield k, b + 20, w, h


def to_image(d):
    from PIL import Image
    full = Image.new("RGBA", (640, 512))
    for k, o, w, h in _tiles(d):
        px = bytearray(d[o:o + w * h * 4])
        for i in range(3, len(px), 4):
            px[i] = min(255, px[i] * 2)
        full.paste(Image.frombytes("RGBA", (w, h), bytes(px)), TILES[k])
    return full


def from_image(d, full):
    d = bytearray(d)
    for k, o, w, h in _tiles(d):
        x, y = TILES[k]
        px = bytearray(full.crop((x, y, x + w, y + h)).tobytes())
        for i in range(3, len(px), 4):
            px[i] = (px[i] + 1) // 2
        d[o:o + w * h * 4] = px
    return bytes(d)


def redraw(full):
    from PIL import Image, ImageDraw, ImageFont
    x0, y0, x1, y1 = BOX
    im = full.copy()
    p = im.load()
    for y in range(y0, y1):  # background: the plain gradient just right of the box, row by row
        c = tuple(round(sum(p[x1 + k, y][i] for k in range(4)) / 4) for i in range(4))
        for x in range(x0, x1):
            p[x, y] = c
    f = ImageFont.truetype(FONT, SIZE)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    l, t, r, btm = dr.textbbox((0, 0), TEXT, font=f)
    tx = x0 + (x1 - x0 - (r - l)) // 2 - l
    ty = y0 + (y1 - y0 - (btm - t)) // 2 - t
    dr.text((tx + 1, ty + 1), TEXT, font=f, fill=(20, 30, 90, 150))   # soft shadow like the logo's
    dr.text((tx, ty), TEXT, font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(im, layer)


def apply(files, lzs_decompress, lzs_compress):
    """Returns [(member, old, new), ...] for fix_sum."""
    old = files[MEMBER]
    d = lzs_decompress(old) if old[:4] == b"LZS\0" else old
    new = from_image(d, redraw(to_image(d)))
    files[MEMBER] = lzs_compress(new) if old[:4] == b"LZS\0" else new
    out = [(MEMBER, old, files[MEMBER])]
    # The title screen actually draws from title_eb.eb (#42), which embeds its own copy of the LZS texture at
    # EB_TEX, with the padded length in the word at EB_LEN. Swap in the edited copy.
    eb = files[EB_MEMBER]
    at = struct.unpack_from("<I", eb, 0x14)[0]
    assert at == EB_TEX and eb[at:at + len(old)] == old, "title_eb.eb layout changed"
    blob = files[MEMBER] + b"\0" * (-len(files[MEMBER]) % 4)
    neb = bytearray(eb[:at] + blob)
    struct.pack_into("<I", neb, EB_LEN, len(blob))
    files[EB_MEMBER] = bytes(neb)
    out.append((EB_MEMBER, eb, files[EB_MEMBER]))
    return out


if __name__ == "__main__":
    sys.path.insert(0, os.environ.get("RHTK", os.path.join(HERE, "..", "toolkit")))
    from c3pac import lzs_decompress, pac_read
    from rhtk import ps2
    with ps2.Iso(sys.argv[1]) as iso:
        m = pac_read(iso.read_file("ALLDATA.PAC"))[MEMBER]
    d = lzs_decompress(m) if m[:4] == b"LZS\0" else m
    redraw(to_image(d)).convert("RGB").save(sys.argv[2])
