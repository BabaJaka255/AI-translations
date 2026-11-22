"""Proof of concept: add the Latin letters the 'large' font lacks, copied from the name-entry font.

Usage: python3 font_proof.py <extracted disc dir> <out dir>
Writes <out>/ALLDATA.PAC and <out>/SLPM_623.22 (with the new glyph entries; test strings are added separately).
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from c3font import FONTS, code_of, fw, idx, set_entry, table, tex_tims  # noqa: E402
from c3pac import fix_sum, lzs_compress, lzs_decompress, pac_build, pac_read  # noqa: E402
from c3tex import tim_image, tim_parse  # noqa: E402

disc, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
elf = bytearray(open(os.path.join(disc, "SLPM_623.22"), "rb").read())
pac_raw = open(os.path.join(disc, "ALLDATA.PAC"), "rb").read()
files = pac_read(pac_raw)
NAMES = [m.decode() for m in pac_raw[12 + 8 * len(files):struct.unpack_from("<I", pac_raw, 12)[0]].split(b"\0") if m]
tf_i, sn_i = NAMES.index("truefont.tex"), NAMES.index("sel_name.tex")
tf = bytearray(lzs_decompress(files[tf_i]))
sn = lzs_decompress(files[sn_i])

large, name = table(elf, "large"), table(elf, "name")
_, _, lfirst, _, lh = FONTS["large"]
_, _, nfirst, _, nh = FONTS["name"]
want = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!?.,-"
        if large[idx(code_of(fw(c)))][0] == 0xFF and name[idx(code_of(fw(c)))][0] != 0xFF]
print("adding", "".join(want))

# page 2 of the large font: TIM #2 (256 x 128, 4bpp); rows 0-2 used, rows 3-4 free
page_off = tex_tims(tf)[lfirst + 2][0]
p = tim_parse(tf, page_off)
w = 256  # page width in pixels
img_off = p["img_off"]
name_pages = {}


def name_px(e):
    if e[0] not in name_pages:
        name_pages[e[0]] = tim_image(sn, tex_tims(sn)[nfirst + e[0]][0])
    return name_pages[e[0]]


def put(x, y, v):
    o = img_off + (y * w + x) // 2
    if x & 1:
        tf[o] = (tf[o] & 0x0F) | (v << 4)
    else:
        tf[o] = (tf[o] & 0xF0) | v


# free spans on page 2: the tail of rows 0-2 and all of rows 3-4
ends = {}
for e in large:
    if e[0] == 2:
        ends[e[2]] = max(ends.get(e[2], 0), e[1] + e[3])
free = {r: ends.get(r, 0) for r in range(5)}  # next free x per row
for c in sorted(want, key=lambda c: -name[idx(code_of(fw(c)))][3]):  # widest first
    code = code_of(fw(c))
    e = name[idx(code)]
    gw = e[3]
    row = next((r for r in range(5) if free[r] + gw <= 256), None)
    if row is None:
        print("no room for", c)
        continue
    x = free[row]
    src = name_px(e)
    for gy in range(lh):  # copy 24 of the 26 rows, shifted up 1 (drops one padding row top and bottom)
        for gx in range(gw):
            put(x + gx, row * lh + gy, src.getpixel((e[1] + gx, e[2] * nh + gy + 1)))
    set_entry(elf, "large", code, (2, x, row, gw))
    free[row] = x + gw

# Space advance: the draw (0x1BB910) and measure routines hard-code 15 px for ' ' and '　'. 6 px suits English.
SPACE_PX = 6
for a in (0x1BB9F0, 0x1BBA2C, 0x1BBF8C, 0x1BBFC8, 0x1BC920, 0x1BC95C, 0x1BCCF8, 0x1BCD34):
    o = a - 0x110000 + 0x1000
    w = struct.unpack_from("<I", elf, o)[0]
    assert w & 0xFFFF in (0xF, SPACE_PX), hex(a)
    struct.pack_into("<I", elf, o, (w & 0xFFFF0000) | SPACE_PX)

old = files[tf_i]
files[tf_i] = lzs_compress(bytes(tf))
print("checksum records updated:", fix_sum(elf, old, files[tf_i]))
first = struct.unpack_from("<I", pac_raw, 12)[0]
new = pac_build(files, first=first, header=pac_raw[:first])
open(os.path.join(out, "ALLDATA.PAC"), "wb").write(new)
open(os.path.join(out, "SLPM_623.22"), "wb").write(elf)
print("ALLDATA.PAC", len(pac_raw), "->", len(new))
