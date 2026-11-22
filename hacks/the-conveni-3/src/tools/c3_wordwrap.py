"""Word wrap for text laid out by 0x166670: the Fixture details panel description (and 7 other callers).

The panel (0x157D08) runs the description through the half-to-full-width converter (0x160B48 -> 0x160958), so
ASCII spaces become 0x8140 and every glyph is a 2-byte cell, then 0x166670 places cells (8-byte records on its
stack: 2 text bytes, x at +4, y at +6; base x at sp+0x400) and starts a new line before a cell that would pass
the right edge. Before breaking it backs up while the cell that would start the new line "can't start a line"
(call at 0x1667EC to the kinsoku check 0x1696B8, a0 = that cell's bytes read little-endian, s0 = the record of
the cell before it). English split mid-word ("alsotak/es").

Pair glyphs that hold a space get their own code pages (picker() below, used by c3_glyphs.build):
  lead 0x88: the blank glyph and pairs that END with a space ("e "),
  lead 0x89: pairs that START with a space (" w"); its two kept kanji are harmless here,
  other pairs: lead 0x8A and up.
The call now goes to a stub that allows a break before the cell when it is a " w" pair (lead 0x89) or a
full-width space 0x8140, or when the cell before it is 0x8140, the blank or an "e " pair (lead 0x88). So every space in
English text is a break point. To never back past the line start (an empty line would loop forever) it also
allows the break when the previous cell is the first of its line. It lives in the dead tail of the old funds code
after the /Gn stubs.
"""
import struct

import c3_glyphs as G
from c3_yen import Asm, DELTA

BASE = 0x112C50             # after the /Gn stubs (tools/c3_gcode.py)
LIMIT = 0x112C98            # the old funds function's epilogue starts here (c3_yen.money_window)
CALL = 0x1667EC
KINSOKU = 0x1696B8
TS_PAGE, LS_PAGE = 0x88, 0x89


def patch(elf):
    a = Asm(BASE)
    a.addiu("v0", "zero", 1)
    a.i(12, "a0", "t1", 0xFF)           # andi t1, a0, 0xff: lead byte of the cell
    a.i(14, "t1", "t1", LS_PAGE)        # xori
    a.beq("t1", "zero", "yes")          # " w" pair
    a.i(37, "s0", "t2", 0)              # delay: lhu t2, 0(s0): the previous cell
    a.ori("t3", "zero", 0x4081)         # 0x8140 read little-endian
    a.beq("t2", "t3", "yes")            # after a full-width space
    a.i(12, "t2", "t2", 0xFF)           # delay: andi: its lead byte
    a.i(14, "t2", "t2", TS_PAGE)        # xori
    a.beq("t2", "zero", "yes")          # after the blank or an "e " pair
    a.i(33, "s0", "t1", 4)              # delay: lh t1, 4(s0): x of the previous cell
    a.beq("a0", "t3", "yes")            # before a full-width space
    a.lw("t3", 0x400, "sp")             # delay: the line's left x
    a.emit(0x54000000 | (9 << 21) | (11 << 16) | 1)  # bnel t1, t3, yes (+1): not the line's first cell
    a.r("zero", "zero", "v0", 0, 0x25)  # likely delay: or v0, zero, zero -> 0
    a.label("yes")
    a.jr("ra")
    a.nop()
    blob = a.finish([])
    assert BASE + len(blob) <= LIMIT, hex(BASE + len(blob))
    o = BASE - DELTA
    elf[o:o + len(blob)] = blob
    c = CALL - DELTA
    assert struct.unpack_from("<I", elf, c)[0] == 0x0C000000 | (KINSOKU >> 2)
    struct.pack_into("<I", elf, c, 0x0C000000 | (BASE >> 2))
    return len(blob)


def _page(p):
    return TS_PAGE if p == " " or p.endswith(" ") else LS_PAGE if p.startswith(" ") else None


def picker():
    """Code chooser for c3_glyphs.build(pick=...): space pairs on their own lead pages (see above)."""
    keep = {G.code_of(k) for k in G.KEEP_KANJI}
    free = [c for c in G._codes() if c not in keep]
    pages = {TS_PAGE: iter([c for c in free if c >> 8 == TS_PAGE]),
             LS_PAGE: iter([c for c in free if c >> 8 == LS_PAGE]),
             None: iter([c for c in free if c >> 8 not in (TS_PAGE, LS_PAGE)])}
    return lambda p: next(pages[_page(p)], None)


def check(mapping):
    assert mapping[" "] == 0x889F
    for p, c in mapping.items():
        want = _page(p)
        assert (c >> 8 == want) if want else (c >> 8 not in (TS_PAGE, LS_PAGE)), (p, hex(c))
