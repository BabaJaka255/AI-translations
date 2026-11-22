"""Word wrap for the Fixture details panel (and any text laid out by 0x166670 that starts with "/A").

0x166670 lays text out in 2-byte cells (an 8-byte record each on its stack: 2 bytes of text, x, y), measures
each, and when a cell would pass the right edge it starts a new line. Before that it backs up while the cell
that would start the new line is in the "can't start a line" list (0x1696B8, Japanese kinsoku). The details
panel strips /n first (0x1BE3E0), so English used to break mid-word ("alsotake/s").

The call at 0x1667EC goes to a stub instead. For text that starts with the marker "/A" (a no-op code to the
drawer and the measurer) the stub only allows a break before or after the blank glyph (the 2-byte space,
c3_glyphs mapping " "); the backing up then stops at a word boundary. It also stops at record 1, so it can
never back past the start. Other text goes to the original check. Marked text must be encoded with 2-byte
spaces and no pair glyph that holds a space, so every cell is a whole glyph and every space a cell
(encode_marked). The stub sits after the /Gn stubs (tools/c3_gcode.py) in the old funds code.
"""
import struct

import c3_glyphs as G
from c3_yen import Asm, DELTA

BASE = 0x112C50
LIMIT = 0x112C94
CALL = 0x1667EC
KINSOKU = 0x1696B8
MARK = "/A"


def patch(elf, blank):
    """blank: the blank glyph's Shift-JIS code (lead << 8 | trail)."""
    le = ((blank & 0xFF) << 8) | (blank >> 8)  # how the cell's two bytes read as a halfword
    a = Asm(BASE)
    a.i(37, "sp", "t0", 0)              # lhu t0, 0(sp): record 0's two bytes
    a.addiu("t1", "zero", 0x412F)       # "/A"
    a.bne("t0", "t1", "orig")
    a.ori("t1", "zero", le)             # delay slot
    a.beq("a0", "t1", "yes")            # the cell that would start the line is a space
    a.addiu("v0", "zero", 1)
    a.beq("s0", "sp", "yes")            # previous record is the marker: stop
    a.i(37, "s0", "t0", 0)              # lhu t0, 0(s0): previous cell
    a.beq("t0", "t1", "yes")            # previous cell is a space
    a.nop()
    a.addiu("v0", "zero", 0)
    a.label("yes")
    a.jr("ra")
    a.nop()
    a.label("orig")
    a.j(KINSOKU)
    a.nop()
    blob = a.finish([])
    assert BASE + len(blob) <= LIMIT, hex(BASE + len(blob))
    o = BASE - DELTA
    elf[o:o + len(blob)] = blob
    c = CALL - DELTA
    assert struct.unpack_from("<I", elf, c)[0] == 0x0C000000 | (KINSOKU >> 2)
    struct.pack_into("<I", elf, c, 0x0C000000 | (BASE >> 2))
    return len(blob)


def encode_marked(text, pairs):
    """"/A" + text, every space the blank glyph, no pair glyph with a space in it."""
    m = {k: v for k, v in pairs.items() if k == " " or " " not in k}
    return G.encode(MARK + text.replace("/n", " ").replace("/L", " "), m, talk=True)
