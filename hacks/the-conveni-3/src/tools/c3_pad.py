"""New text code /Qn: draw number param n with at least 2 digits (the clock: "AM 7:06" instead of "AM 7:6").

The text drawer 0x1BB910 and the width measurer 0x1BC8C8 dispatch "/" codes through jump tables (draw 0x5417A0,
measure 0x541860; one word per character '0'..'W', lower case is folded to upper case). "/0".."/9" print number
param n (RAM 0x41F158 + 4n) with the number-to-full-width routine 0x1BABA0(out, value, min_digits), always with
min_digits 0. No script text uses "/Q", so its two table slots (no-ops before) point at two stubs that read the
digit after Q and make the same call with min_digits 2. The stubs sit after the yen helper (tools/c3_yen.py) in
the unused tail of the old funds display code. patch(elf) is called by c3_build after c3_yen.patch.
"""
import struct

from c3_yen import Asm, DELTA

STUBS = 0x112BA0            # free after the yen helper (ends 0x112B98); the tail is free up to 0x112C94
LIMIT = 0x112C94
NUM = 0x1BABA0              # number -> full-width digits
DRAW_TABLE, MEAS_TABLE = 0x5417A0, 0x541860
DRAW_BACK, MEAS_BACK = 0x1BBEC4, 0x1BCC3C   # "jal draw/measure(buffer)" right after the /n case's NUM call
NOOP_DRAW, NOOP_MEAS = 0x1BC674, 0x1BCF7C
SLOT = ord("Q") - 0x30


def stub(a, ptr, back, buf_off):
    a.i(36, ptr, "a0", 0)          # lbu a0, 0(ptr): the param digit
    a.addiu(ptr, ptr, 1)
    a.sll("v0", "a0", 2)
    a.addiu("a0", "sp", buf_off)   # same buffer the /n case uses
    a.lui("a1", 0x42)
    a.addu("a1", "a1", "v0")
    a.lw("a1", -0xF68, "a1")       # params[digit] (0x41F158 + 4 * (digit - '0'))
    a.jal(NUM)
    a.addiu("a2", "zero", 2)       # at least 2 digits
    a.j(back)
    a.nop()


def patch(elf):
    a = Asm(STUBS)
    stub(a, "s1", DRAW_BACK, 0x10)
    meas = a.pc()
    stub(a, "s0", MEAS_BACK, 0)
    blob = a.finish([])
    assert STUBS + len(blob) <= LIMIT
    o = STUBS - DELTA
    # dead code of the old funds display (never reached once c3_yen rewrote its start)
    elf[o:o + len(blob)] = blob
    for table, old, new in ((DRAW_TABLE, NOOP_DRAW, STUBS), (MEAS_TABLE, NOOP_MEAS, meas)):
        f = table - DELTA + 4 * SLOT
        assert struct.unpack_from("<I", elf, f)[0] == old, hex(table)
        struct.pack_into("<I", elf, f, new)
    return len(blob)
