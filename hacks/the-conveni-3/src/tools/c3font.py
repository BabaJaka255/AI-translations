"""Font tables for The Conveni 3.

Each font has a glyph table in the ELF: one 4-byte entry per Shift-JIS code, index = code - 0x813F
(code <= 0xE03F) or code - 0xC190, 0x2912 entries. Entry = (page, x, row, width); page 0xFF = no glyph.
Glyph = page TIM, rectangle (x, row*h, width, h).
"""
import struct
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from c3tex import tim_image, tim_parse  # noqa: E402

ELF_VADDR, ELF_FOFF = 0x205700, 0xF6700
N = 0x2912
FONTS = {  # name: (table vaddr, tex file in ALLDATA, first TIM index in that TEX, pages, row height)
    "small": (0x258BF0, "truefont.tex", 3, 3, 20),
    "large": (0x263038, "truefont.tex", 0, 3, 24),
    "talk": (0x26BC50, "truefont.tex", 6, 3, 28),
    "name": (0x276098, "sel_name.tex", 0, 5, 26),
}


def idx(code):
    return code - 0x813F if code <= 0xE03F else code - 0xC190


def code_of(ch):
    return int.from_bytes(ch.encode("cp932"), "big")


def fw(s):
    """ASCII -> full-width Shift-JIS characters (space -> ideographic space)."""
    return "".join("　" if c == " " else chr(ord(c) + 0xFEE0) if 33 <= ord(c) < 127 else c for c in s)


def table(elf, name):
    o = FONTS[name][0] - ELF_VADDR + ELF_FOFF
    return [tuple(elf[o + 4 * i:o + 4 * i + 4]) for i in range(N)]


def set_entry(elf: bytearray, name, code, entry):
    o = FONTS[name][0] - ELF_VADDR + ELF_FOFF + 4 * idx(code)
    elf[o:o + 4] = bytes(entry)


def tex_tims(tex):
    """[(offset, size)] for every TIM in a TEX, in order."""
    n, = struct.unpack_from("<I", tex, 8)
    return [struct.unpack_from("<II", tex, 0x14 + 8 * i) for i in range(n)]
