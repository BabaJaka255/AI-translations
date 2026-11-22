"""New text code /Gn: draw number param n as money with commas ("¥45,000"), through the yen formatter.

Edit Interior's fixture panel prints "Price ¥/0" and "Upkeep ¥/1／mo" from raw params ("¥45000"). Like /Qn
(tools/c3_pad.py), "/G" had no-op slots in the draw (0x5417A0) and measure (0x541860) code tables; two stubs read
the digit and call the formatter 0x1447F0(amount, buffer, suffix 0) (tools/c3_yen.py), which writes the
full-width "¥45,000" into the same stack buffer the /n case draws from, then rejoin that case. The stubs sit
after the /Qn stubs. patch(elf) runs after c3_yen and c3_pad.
"""
import struct

from c3_yen import Asm, DELTA

BASE = 0x112BF8             # right after the /Qn stubs; the word-wrap stub follows (tools/c3_wordwrap.py)
LIMIT = 0x112C94
FMT = 0x1447F0
DRAW_TABLE, MEAS_TABLE = 0x5417A0, 0x541860
DRAW_BACK, MEAS_BACK = 0x1BBEC4, 0x1BCC3C
NOOP_DRAW, NOOP_MEAS = 0x1BC674, 0x1BCF7C
SLOT = ord("G") - 0x30


def stub(a, ptr, back, buf_off):
    a.i(36, ptr, "a0", 0)          # lbu a0, 0(ptr): the param digit
    a.addiu(ptr, ptr, 1)
    a.sll("v0", "a0", 2)
    a.lui("a0", 0x42)
    a.addu("a0", "a0", "v0")
    a.lw("a0", -0xF68, "a0")       # params[digit] (0x41F158 + 4 * (digit - '0')), sign-extended to 64 bits
    a.addiu("a1", "sp", buf_off)
    a.jal(FMT)
    a.addiu("a2", "zero", 0)       # no suffix
    a.j(back)
    a.nop()


def patch(elf):
    a = Asm(BASE)
    stub(a, "s1", DRAW_BACK, 0x10)
    meas = a.pc()
    stub(a, "s0", MEAS_BACK, 0)
    blob = a.finish([])
    assert BASE + len(blob) <= LIMIT
    o = BASE - DELTA
    elf[o:o + len(blob)] = blob
    for table, old, new in ((DRAW_TABLE, NOOP_DRAW, BASE), (MEAS_TABLE, NOOP_MEAS, meas)):
        f = table - DELTA + 4 * SLOT
        assert struct.unpack_from("<I", elf, f)[0] == old, hex(table)
        struct.pack_into("<I", elf, f, new)
    return len(blob)
