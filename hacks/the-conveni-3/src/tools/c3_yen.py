"""Money in Western style: replace the game's yen formatter (2億3000万円) with one that prints ¥230,000,000.

The formatter at 0x1447F0 takes a0 = amount (64-bit), a1 = output buffer, a2 = suffix (0 none, 1 per month,
2 per day). It builds ASCII in a scratch buffer and runs the game's half-to-full-width converter (0x160958), so
ASCII ',' and '-' come out as full-width glyphs. The new routine fits inside the old one (0x2A0 bytes) with its
strings stored after the code. patch(elf) is called by c3_build.
"""
import struct

BASE = 0x1447F0          # vaddr of the formatter
END = 0x144A90           # first byte after it
DELTA = 0x10F000         # vaddr - file offset
STRCAT, SPRINTF, DIVDI3, MODDI3, HAN2ZEN = 0x1F4050, 0x1F3FC0, 0x1EF398, 0x1EFA30, 0x160958

R = {n: i for i, n in enumerate("zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split())}


class Asm:
    def __init__(self, base):
        self.base, self.code, self.labels, self.fix = base, [], {}, []

    def pc(self):
        return self.base + 4 * len(self.code)

    def label(self, n):
        self.labels[n] = self.pc()

    def emit(self, w):
        self.code.append(w & 0xFFFFFFFF)

    def i(self, op, rs, rt, imm):
        self.emit(op << 26 | R[rs] << 21 | R[rt] << 16 | (imm & 0xFFFF))

    def r(self, rs, rt, rd, sa, fn):
        self.emit(R[rs] << 21 | R[rt] << 16 | R[rd] << 11 | sa << 6 | fn)

    # instructions
    def nop(self): self.emit(0)
    def addiu(self, rt, rs, imm): self.i(9, rs, rt, imm)
    def ori(self, rt, rs, imm): self.i(13, rs, rt, imm)
    def lui(self, rt, imm): self.i(15, "zero", rt, imm)
    def sd(self, rt, off, base): self.i(63, base, rt, off)
    def ld(self, rt, off, base): self.i(55, base, rt, off)
    def sb(self, rt, off, base): self.i(40, base, rt, off)
    def move(self, rd, rs): self.r(rs, "zero", rd, 0, 0x2D)          # daddu
    def dsubu(self, rd, rs, rt): self.r(rs, rt, rd, 0, 0x2F)
    def sll(self, rd, rt, sa): self.r("zero", rt, rd, sa, 0)
    def divu(self, rs, rt): self.r(rs, rt, "zero", 0, 0x1B)
    def mflo(self, rd): self.r("zero", "zero", rd, 0, 0x12)
    def mfhi(self, rd): self.r("zero", "zero", rd, 0, 0x10)
    def addu(self, rd, rs, rt): self.r(rs, rt, rd, 0, 0x21)
    def daddu(self, rd, rs, rt): self.r(rs, rt, rd, 0, 0x2D)
    def mult(self, rs, rt): self.r(rs, rt, "zero", 0, 0x18)
    def dsll(self, rd, rt, sa): self.r("zero", rt, rd, sa, 0x38)
    def dsll32(self, rd, rt, sa): self.r("zero", rt, rd, sa, 0x3C)
    def dsrl32(self, rd, rt, sa): self.r("zero", rt, rd, sa, 0x3E)
    def lw(self, rt, off, base): self.i(35, base, rt, off)
    def j(self, target): self.emit(2 << 26 | (target >> 2) & 0x3FFFFFF)

    def jr(self, rs): self.r(rs, "zero", "zero", 0, 0x08)
    def jal(self, target): self.emit(3 << 26 | (target >> 2) & 0x3FFFFFF)

    def br(self, op, rs, rt, lab):
        self.fix.append((len(self.code), lab))
        self.i(op, rs, rt, 0)

    def beq(self, rs, rt, lab): self.br(4, rs, rt, lab)
    def bne(self, rs, rt, lab): self.br(5, rs, rt, lab)
    def b(self, lab): self.br(4, "zero", "zero", lab)

    def bgez(self, rs, lab):
        self.fix.append((len(self.code), lab))
        self.emit(1 << 26 | R[rs] << 21 | 1 << 16)

    def la(self, rt, lab):  # filled in after layout
        self.fix.append((len(self.code), ("hi", lab)))
        self.lui(rt, 0)
        self.fix.append((len(self.code), ("lo", lab)))
        self.addiu(rt, rt, 0)

    def call(self, target):
        self.jal(target)
        self.nop()

    def finish(self, data):
        for k, (name, s) in enumerate(data):
            self.labels[name] = self.pc() + sum(len(x) for _, x in data[:k])
        blob = b"".join(s for _, s in data)
        for idx, lab in self.fix:
            w = self.code[idx]
            if isinstance(lab, tuple):
                kind, n = lab
                v = self.labels[n]
                part = ((v + 0x8000) >> 16) if kind == "hi" else (v & 0xFFFF)
                self.code[idx] = (w & 0xFFFF0000) | part
            else:
                off = (self.labels[lab] - (self.base + 4 * idx + 4)) >> 2
                self.code[idx] = (w & 0xFFFF0000) | (off & 0xFFFF)
        return b"".join(struct.pack("<I", w) for w in self.code) + blob


def build():
    a = Asm(BASE)
    a.addiu("sp", "sp", -0x150)
    for k, reg in enumerate(("s0", "s1", "s2", "s3", "s4")):
        a.sd(reg, 0x120 + 8 * k, "sp")
    a.sd("ra", 0x148, "sp")
    a.move("s1", "a0")
    a.move("s3", "a1")
    a.move("s2", "a2")
    a.addiu("s4", "sp", 0x20)       # text is built here, sprintf scratch at sp+0
    a.sb("zero", 0, "s4")
    a.bgez("s1", "pos")
    a.nop()
    a.dsubu("s1", "zero", "s1")
    a.move("a0", "s4")
    a.la("a1", "minus")
    a.call(STRCAT)
    a.label("pos")
    a.move("a0", "s4")
    a.la("a1", "yen")
    a.call(STRCAT)
    # billions (64-bit division), then three groups of three digits
    a.move("a0", "s1")
    a.lui("a1", 0x3B9A)
    a.ori("a1", "a1", 0xCA00)        # 1,000,000,000
    a.call(DIVDI3)
    a.sll("s0", "v0", 0)             # s0 = billions; non-zero also means "digits started"
    a.move("a0", "s1")
    a.lui("a1", 0x3B9A)
    a.ori("a1", "a1", 0xCA00)
    a.call(MODDI3)
    a.sll("s1", "v0", 0)             # s1 = rest, < 1e9
    a.beq("s0", "zero", "g0")
    a.nop()
    a.move("a0", "sp")
    a.la("a1", "fmt_d")
    a.move("a2", "s0")
    a.call(SPRINTF)
    a.move("a0", "s4")
    a.move("a1", "sp")
    a.call(STRCAT)
    for g, div in enumerate((1000000, 1000, 1)):
        last = div == 1
        a.label(f"g{g}")
        a.lui("t0", div >> 16)
        a.ori("t0", "t0", div & 0xFFFF)
        a.divu("s1", "t0")
        a.nop()
        a.nop()
        a.mflo("t1")
        a.mfhi("t2")
        a.sll("s1", "t2", 0)
        a.bne("s0", "zero", f"c{g}")
        a.nop()
        if not last:
            a.beq("t1", "zero", f"g{g + 1}")
            a.nop()
        a.la("a1", "fmt_d")
        a.addiu("s0", "zero", 1)
        a.b(f"p{g}")
        a.nop()
        a.label(f"c{g}")
        a.la("a1", "fmt_c")
        a.label(f"p{g}")
        a.move("a0", "sp")
        a.move("a2", "t1")
        a.call(SPRINTF)
        a.move("a0", "s4")
        a.move("a1", "sp")
        a.call(STRCAT)
    a.label("g3")
    a.addiu("t0", "zero", 1)
    a.beq("s2", "t0", "mo")
    a.nop()
    a.addiu("t0", "zero", 2)
    a.bne("s2", "t0", "out")
    a.nop()
    a.la("a1", "day")
    a.b("cat")
    a.nop()
    a.label("mo")
    a.la("a1", "mo_s")
    a.label("cat")
    a.move("a0", "s4")
    a.call(STRCAT)
    a.label("out")
    a.move("a0", "s3")
    a.move("a1", "s4")
    a.call(HAN2ZEN)
    a.move("v0", "s3")
    for k, reg in enumerate(("s0", "s1", "s2", "s3", "s4")):
        a.ld(reg, 0x120 + 8 * k, "sp")
    a.ld("ra", 0x148, "sp")
    a.jr("ra")
    a.addiu("sp", "sp", 0x150)
    data = [("minus", b"-\0"), ("yen", b"\x81\x8f\0"), ("fmt_d", b"%d\0"), ("fmt_c", b",%03d\0"),
            ("mo_s", b"\x81\x5emo\0"), ("day", b"\x81\x5eday\0")]
    blob = a.finish(data)
    assert len(blob) <= END - BASE, (len(blob), END - BASE)
    return blob


DRAW = 0x1BB910                 # draw a text string at the current position
H1 = 0x112B18                   # helper: draw the amount held in the game's number params (in 10,000s)


def money_window():
    """0x112AF8: the funds display. Format the amount (s3) with the new routine and draw it."""
    a = Asm(0x112AF8)
    a.move("a0", "s3")
    a.move("a1", "sp")
    a.jal(BASE)
    a.move("a2", "zero")
    a.jal(DRAW)
    a.move("a0", "sp")
    a.b("epi")
    a.ld("s0", 0x30, "sp")
    a.labels["epi"] = 0x112C98
    blob = a.finish([])
    assert a.pc() <= H1
    return blob


def helper():
    """Draw params[1]*10000 + params[0] (an amount counted in 10,000 yen) as ¥ text."""
    a = Asm(H1)
    a.addiu("sp", "sp", -0x50)
    a.sd("ra", 0x48, "sp")
    a.lui("t0", 0x42)
    a.addiu("t0", "t0", -0xEA8)
    a.lw("t1", 4, "t0")
    a.lw("t2", 0, "t0")
    a.addiu("t3", "zero", 10000)
    a.mult("t1", "t3")
    a.nop()
    a.nop()
    a.mflo("t1")
    a.addu("t1", "t1", "t2")
    a.dsll32("a0", "t1", 0)
    a.dsrl32("a0", "a0", 0)          # zero-extended amount in 10,000s
    a.dsll("t4", "a0", 13)           # x 10000 = 8192 + 1024 + 512 + 256 + 16
    for sh in (10, 9, 8, 4):
        a.dsll("t5", "a0", sh)
        a.daddu("t4", "t4", "t5")
    a.move("a0", "t4")
    a.move("a1", "sp")
    a.jal(BASE)
    a.move("a2", "zero")
    a.jal(DRAW)
    a.move("a0", "sp")
    a.ld("ra", 0x48, "sp")
    a.jr("ra")
    a.addiu("sp", "sp", 0x50)
    blob = a.finish([])
    assert a.pc() <= 0x112C94
    return blob


def call_site(at, tail):
    """Replace a 億/万 drawing branch with a call to the helper, then the given tail instructions."""
    a = Asm(at)
    a.jal(H1)
    a.nop()
    tail(a)
    return a.finish([])


def patch(elf):
    o = BASE - DELTA
    old = struct.unpack_from("<I", elf, o)[0]
    assert old == 0x27BDFEB0, hex(old)   # addiu sp, sp, -0x150
    blob = build()
    elf[o:o + len(blob)] = blob
    elf[o + len(blob):END - DELTA] = b"\0" * (END - BASE - len(blob))

    def put(vaddr, data, expect):
        f = vaddr - DELTA
        assert struct.unpack_from("<I", elf, f)[0] == expect, (hex(vaddr), hex(struct.unpack_from("<I", elf, f)[0]))
        elf[f:f + len(data)] = data

    put(0x112AF8, money_window(), 0x16600007)            # bnez s3, ...
    h = helper()  # lands in the now unused tail of the old funds display code
    elf[H1 - DELTA:H1 - DELTA + len(h)] = h

    def t1(a):  # 0x1161ac: continue at 0x1161ec with a1 = 0x146
        a.labels["k"] = 0x1161EC
        a.b("k")
        a.addiu("a1", "zero", 0x146)

    def t2(a):  # 0x11626c: continue at 0x1162ac with a0 = 0x250000
        a.labels["k"] = 0x1162AC
        a.b("k")
        a.lui("a0", 0x25)

    def t3(a):  # 0x11ca64: return from the small draw function
        a.ld("s0", 0, "sp")
        a.ld("ra", 8, "sp")
        a.jr("ra")
        a.addiu("sp", "sp", 0x10)

    put(0x1161A4, call_site(0x1161A4, t1), 0x8E020004)   # lw v0, 4(s0)
    put(0x116264, call_site(0x116264, t2), 0x8E020004)
    put(0x11CA5C, call_site(0x11CA5C, t3), 0x3C040052)   # lui a0, 0x52
    return len(blob)


if __name__ == "__main__":
    print(len(build()), "bytes of", END - BASE)
