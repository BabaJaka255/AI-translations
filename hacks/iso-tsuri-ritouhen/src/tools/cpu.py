"""Minimal 65816 interpreter for tracing SNES (HiROM) code from a snes9x save state.
Not cycle accurate. I/O is stubbed: multiply/divide, VRAM port, WRAM port, DMA (to $2118/$2180/$2104/$2122)."""
import re

def blocks(d):
    out = {}; i = d.index(b'\n') + 1
    while i < len(d):
        m = re.match(rb'([A-Z]{3}):(\d{6}):', d[i:i+11])
        if not m: break
        n = int(m.group(2)); out[m.group(1).decode()] = d[i+11:i+11+n]; i += 11 + n
    return out

class Halt(Exception): pass

class SNES:
    def __init__(self, rom, state=None):
        self.rom = rom
        self.wram = bytearray(0x20000)
        self.sram = bytearray(0x2000)
        self.vram = bytearray(0x10000)
        self.cgram = bytearray(0x200)
        self.io = bytearray(0x10000)
        self.vaddr = 0; self.vinc = 1; self.vinc_hi = True
        self.waddr = 0
        self.mul = 0; self.div = 0
        self.read_hooks = []   # f(addr24, val)
        self.write_hooks = []  # f(addr24, val)
        self.exec_hooks = {}   # pc24 -> f(cpu)
        self.trace = None
        self.joy = 0
        self.frame_toggle = 0
        self.A = 0; self.X = 0; self.Y = 0; self.S = 0x1ff; self.D = 0; self.DB = 0; self.PB = 0; self.PC = 0
        self.P = 0x34; self.E = 0
        if state:
            b = blocks(state)
            self.wram[:] = b['RAM']; self.vram[:] = b['VRA']
            self.sram[:] = b['SRA'][:0x2000]
            r = b['REG']
            self.PB = r[0]; self.DB = r[1]
            self.P = int.from_bytes(r[2:4], 'big') & 0xff
            self.A = int.from_bytes(r[4:6], 'big'); self.D = int.from_bytes(r[6:8], 'big')
            self.S = int.from_bytes(r[8:10], 'big'); self.X = int.from_bytes(r[10:12], 'big')
            self.Y = int.from_bytes(r[12:14], 'big'); self.PC = int.from_bytes(r[14:16], 'big')
        self.cycles = 0
        self.infetch = False

    # ---------------- memory ----------------
    def romoff(self, bank, addr):
        return ((bank & 0x3f) << 16 | addr) % len(self.rom)

    def rd(self, a):
        a &= 0xffffff; bank = a >> 16; addr = a & 0xffff
        if bank in (0x7e, 0x7f):
            v = self.wram[a - 0x7e0000]
        elif bank >= 0xc0 or 0x40 <= bank < 0x7e:
            v = self.rom[self.romoff(bank, addr)]
        else:
            if addr < 0x2000: v = self.wram[addr]
            elif addr >= 0x8000: v = self.rom[self.romoff(bank, addr)]
            elif 0x6000 <= addr < 0x8000 and (bank & 0x7f) >= 0x20: v = self.sram[addr - 0x6000]
            else: v = self.ioread(addr)
        for h in self.read_hooks: h(a, v)
        return v

    def wr(self, a, v):
        a &= 0xffffff; bank = a >> 16; addr = a & 0xffff; v &= 0xff
        for h in self.write_hooks: h(a, v)
        if bank in (0x7e, 0x7f): self.wram[a - 0x7e0000] = v
        elif bank >= 0xc0 or 0x40 <= bank < 0x7e: pass
        else:
            if addr < 0x2000: self.wram[addr] = v
            elif addr >= 0x8000: pass
            elif 0x6000 <= addr < 0x8000 and (bank & 0x7f) >= 0x20: self.sram[addr - 0x6000] = v
            else: self.iowrite(addr, v)

    def ioread(self, addr):
        io = self.io
        if addr == 0x4212:
            self.frame_toggle ^= 1
            return 0x80 if self.frame_toggle else 0x01
        if addr == 0x4210: return 0x80
        if addr == 0x4211: return 0x80
        if addr in (0x4214, 0x4215): return (self.div >> (8 * (addr - 0x4214))) & 0xff
        if addr in (0x4216, 0x4217): return (self.mul >> (8 * (addr - 0x4216))) & 0xff
        if addr == 0x4218: return self.joy & 0xff
        if addr == 0x4219: return self.joy >> 8
        if addr == 0x2180:
            v = self.wram[self.waddr]; self.waddr = (self.waddr + 1) & 0x1ffff; return v
        if addr in (0x2139, 0x213a):
            v = self.vram[(self.vaddr * 2 + (addr - 0x2139)) & 0xffff]
            if (addr == 0x213a) == self.vinc_hi: self.vaddr = (self.vaddr + self.vinc) & 0x7fff
            return v
        return io[addr]

    def iowrite(self, addr, v):
        io = self.io; io[addr] = v
        if addr == 0x2115:
            self.vinc = (1, 32, 128, 128)[v & 3]; self.vinc_hi = bool(v & 0x80)
        elif addr == 0x2116: self.vaddr = (self.vaddr & 0xff00) | v
        elif addr == 0x2117: self.vaddr = (self.vaddr & 0xff) | (v << 8)
        elif addr in (0x2118, 0x2119):
            self.vram[(self.vaddr * 2 + (addr - 0x2118)) & 0xffff] = v
            if (addr == 0x2119) == self.vinc_hi: self.vaddr = (self.vaddr + self.vinc) & 0x7fff
        elif addr == 0x2181: self.waddr = (self.waddr & 0x1ff00) | v
        elif addr == 0x2182: self.waddr = (self.waddr & 0x100ff) | (v << 8)
        elif addr == 0x2183: self.waddr = (self.waddr & 0xffff) | ((v & 1) << 16)
        elif addr == 0x2180: self.wram[self.waddr] = v; self.waddr = (self.waddr + 1) & 0x1ffff
        elif addr == 0x4203: self.mul = io[0x4202] * v
        elif addr == 0x4206:
            dd = io[0x4204] | io[0x4205] << 8
            if v: self.div = dd // v; self.mul = dd % v
            else: self.div = 0xffff; self.mul = dd
        elif addr == 0x420b:
            for ch in range(8):
                if v >> ch & 1: self.dma(ch)

    def dma(self, ch):
        io = self.io; b = 0x4300 + ch * 16
        ctrl = io[b]; dest = io[b + 1]
        src = io[b + 2] | io[b + 3] << 8 | io[b + 4] << 16
        n = io[b + 5] | io[b + 6] << 8 or 0x10000
        mode = ctrl & 7; step = 0 if ctrl & 8 else (-1 if ctrl & 0x10 else 1)
        pat = {0: [0], 1: [0, 1], 2: [0, 0], 3: [0, 0, 1, 1], 4: [0, 1, 2, 3], 5: [0, 1, 0, 1], 6: [0, 0], 7: [0, 0, 1, 1]}[mode]
        hooks = self.read_hooks; self.read_hooks = []
        for i in range(n):
            reg = 0x2100 | ((dest + pat[i % len(pat)]) & 0xff)
            if ctrl & 0x80:
                self.wr(src, self.ioread(reg))
            else:
                val = self.rd(src)
                for h in hooks: h(src, val)
                self.iowrite(reg, val)
            src = (src & 0xff0000) | ((src + step) & 0xffff)
        self.read_hooks = hooks
        io[b + 2] = src & 0xff; io[b + 3] = (src >> 8) & 0xff; io[b + 5] = 0; io[b + 6] = 0

    # ---------------- helpers ----------------
    @property
    def m(self): return bool(self.P & 0x20)
    @property
    def x(self): return bool(self.P & 0x10)

    def fetch(self):
        self.infetch = True
        v = self.rd(self.PB << 16 | self.PC)
        self.infetch = False; self.PC = (self.PC + 1) & 0xffff; return v
    def fetch16(self):
        lo = self.fetch(); return lo | self.fetch() << 8
    def fetch24(self):
        lo = self.fetch16(); return lo | self.fetch() << 16

    def push(self, v):
        self.wr(self.S, v); self.S = (self.S - 1) & 0xffff
    def pull(self):
        self.S = (self.S + 1) & 0xffff; return self.rd(self.S)
    def push16(self, v): self.push(v >> 8); self.push(v & 0xff)
    def pull16(self): lo = self.pull(); return lo | self.pull() << 8

    def rd16(self, a, wrapbank=False):
        lo = self.rd(a)
        if wrapbank: return lo | self.rd((a & 0xff0000) | ((a + 1) & 0xffff)) << 8
        return lo | self.rd(a + 1) << 8
    def rd24(self, a): return self.rd16(a) | self.rd(a + 2) << 16

    def setnz(self, v, wide):
        self.P &= ~0x82 & 0xff
        if wide:
            if v & 0xffff == 0: self.P |= 2
            if v & 0x8000: self.P |= 0x80
        else:
            if v & 0xff == 0: self.P |= 2
            if v & 0x80: self.P |= 0x80

    def flag(self, f, c):
        if c: self.P |= f
        else: self.P &= ~f & 0xff

    # effective address computations -> 24-bit address
    def ea(self, mode):
        D = self.D; DB = self.DB << 16
        if mode == 'd': return (D + self.fetch()) & 0xffff
        if mode == 'dx': return (D + self.fetch() + self.X) & 0xffff
        if mode == 'dy': return (D + self.fetch() + self.Y) & 0xffff
        if mode == 'A': return DB | self.fetch16()
        if mode == 'Ax': return (DB + self.fetch16() + self.X) & 0xffffff
        if mode == 'Ay': return (DB + self.fetch16() + self.Y) & 0xffffff
        if mode == 'L': return self.fetch24()
        if mode == 'Lx': return (self.fetch24() + self.X) & 0xffffff
        if mode == '(d)': return DB | self.rd16((D + self.fetch()) & 0xffff)
        if mode == '(d,x)': return DB | self.rd16((D + self.fetch() + self.X) & 0xffff)
        if mode == '(d),y': return (DB + self.rd16((D + self.fetch()) & 0xffff) + self.Y) & 0xffffff
        if mode == '[d]': return self.rd24((D + self.fetch()) & 0xffff)
        if mode == '[d],y': return (self.rd24((D + self.fetch()) & 0xffff) + self.Y) & 0xffffff
        if mode == 's': return (self.S + self.fetch()) & 0xffff
        if mode == '(s),y': return (DB + self.rd16((self.S + self.fetch()) & 0xffff) + self.Y) & 0xffffff
        raise ValueError(mode)

    def load(self, mode, wide):
        if mode == 'imm':
            return self.fetch16() if wide else self.fetch()
        a = self.ea(mode)
        if wide:
            if mode in ('d', 'dx', 'dy', 's'): return self.rd(a) | self.rd((a + 1) & 0xffff) << 8
            return self.rd(a) | self.rd((a + 1) & 0xffffff) << 8
        return self.rd(a)

    def store(self, a, v, wide, mode=''):
        self.wr(a, v & 0xff)
        if wide:
            if mode in ('d', 'dx', 'dy', 's'): self.wr((a + 1) & 0xffff, v >> 8)
            else: self.wr((a + 1) & 0xffffff, v >> 8)

    def rmw(self, mode, wide, fn):
        if mode == 'acc':
            mask = 0xffff if wide else 0xff
            r = fn(self.A & mask)
            if wide: self.A = r & 0xffff
            else: self.A = (self.A & 0xff00) | (r & 0xff)
            return
        a = self.ea(mode)
        if wide:
            v = self.rd(a) | self.rd((a + 1) & (0xffff if mode in ('d', 'dx') else 0xffffff)) << 8
        else: v = self.rd(a)
        r = fn(v)
        self.store(a, r, wide, mode)

    def adc(self, v):
        wide = not self.m; c = self.P & 1
        a = self.A if wide else self.A & 0xff
        if self.P & 8:
            # decimal
            digits = 4 if wide else 2; res = 0; carry = c
            for i in range(digits):
                s = ((a >> 4*i) & 0xf) + ((v >> 4*i) & 0xf) + carry
                carry = 1 if s > 9 else 0
                if s > 9: s -= 10
                res |= (s & 0xf) << 4*i
            r = res | (carry << (16 if wide else 8))
        else:
            r = a + v + c
        mask = 0xffff if wide else 0xff; sign = 0x8000 if wide else 0x80
        self.flag(0x40, (~(a ^ v) & (a ^ r) & sign) != 0)
        self.flag(1, r > mask)
        r &= mask
        if wide: self.A = r
        else: self.A = (self.A & 0xff00) | r
        self.setnz(r, wide)

    def sbc(self, v):
        wide = not self.m
        if self.P & 8:
            c = self.P & 1; a = self.A if wide else self.A & 0xff
            digits = 4 if wide else 2; res = 0; borrow = 1 - c
            for i in range(digits):
                s = ((a >> 4*i) & 0xf) - ((v >> 4*i) & 0xf) - borrow
                borrow = 1 if s < 0 else 0
                if s < 0: s += 10
                res |= (s & 0xf) << 4*i
            mask = 0xffff if wide else 0xff
            bin_r = a - v - (1 - c)
            sign = 0x8000 if wide else 0x80
            self.flag(0x40, ((a ^ v) & (a ^ bin_r) & sign) != 0)
            self.flag(1, borrow == 0)
            if wide: self.A = res & mask
            else: self.A = (self.A & 0xff00) | (res & 0xff)
            self.setnz(res, wide)
        else:
            self.adc(v ^ (0xffff if wide else 0xff))

    def cmp(self, reg, v, wide):
        mask = 0xffff if wide else 0xff
        r = (reg & mask) - v
        self.flag(1, r >= 0); self.setnz(r & mask, wide)

    def branch(self, cond):
        off = self.fetch()
        if cond:
            if off & 0x80: off -= 0x100
            self.PC = (self.PC + off) & 0xffff

    def fixx(self):
        if self.x: self.X &= 0xff; self.Y &= 0xff

    # ---------------- step ----------------
    def step(self):
        pc24 = self.PB << 16 | self.PC
        h = self.exec_hooks.get(pc24)
        if h: h(self)
        if self.trace: self.trace(self, pc24)
        op = self.fetch()
        self.cycles += 1
        M = not self.m; X = not self.x  # wide flags
        g = GROUP1.get(op)
        if g:
            name, mode = g
            if name == 'STA':
                a = self.ea(mode); self.store(a, self.A, M, mode); return
            v = self.load(mode, M)
            if name == 'ORA': r = (self.A | v);
            elif name == 'AND': r = (self.A & v)
            elif name == 'EOR': r = (self.A ^ v)
            elif name == 'ADC': self.adc(v); return
            elif name == 'SBC': self.sbc(v); return
            elif name == 'CMP': self.cmp(self.A, v, M); return
            elif name == 'LDA': r = v
            if M: self.A = r & 0xffff
            else: self.A = (self.A & 0xff00) | (r & 0xff)
            self.setnz(r, M); return
        f = OPS.get(op)
        if f is None: raise Halt('bad opcode %02X at %06X' % (op, pc24))
        f(self, op)

GROUP1 = {}
_g1 = ["ORA", "AND", "EOR", "ADC", "STA", "LDA", "CMP", "SBC"]
_m1 = {0x01: '(d,x)', 0x03: 's', 0x05: 'd', 0x07: '[d]', 0x09: 'imm', 0x0D: 'A', 0x0F: 'L', 0x11: '(d),y', 0x12: '(d)',
       0x13: '(s),y', 0x15: 'dx', 0x17: '[d],y', 0x19: 'Ay', 0x1D: 'Ax', 0x1F: 'Lx'}
for i, n in enumerate(_g1):
    for o, md in _m1.items():
        if n == 'STA' and md == 'imm': continue
        GROUP1[i * 0x20 + o] = (n, md)

OPS = {}
def op(*codes):
    def deco(f):
        for c in codes: OPS[c] = f
        return f
    return deco

def _w(c): return not c.m
def _xw(c): return not c.x

# flags
@op(0x18)
def _(c, o): c.P &= 0xfe
@op(0x38)
def _(c, o): c.P |= 1
@op(0x58)
def _(c, o): c.P &= ~4 & 0xff
@op(0x78)
def _(c, o): c.P |= 4
@op(0xB8)
def _(c, o): c.P &= ~0x40 & 0xff
@op(0xD8)
def _(c, o): c.P &= ~8 & 0xff
@op(0xF8)
def _(c, o): c.P |= 8
@op(0xC2)
def _(c, o): c.P &= ~c.fetch() & 0xff
@op(0xE2)
def _(c, o): c.P |= c.fetch(); c.fixx()
@op(0xFB)
def _(c, o):
    e = c.E; c.E = c.P & 1; c.flag(1, e)
    if c.E: c.P |= 0x30; c.fixx()

# transfers
@op(0xAA)
def _(c, o): c.X = c.A & (0xffff if _xw(c) else 0xff); c.setnz(c.X, _xw(c))
@op(0xA8)
def _(c, o): c.Y = c.A & (0xffff if _xw(c) else 0xff); c.setnz(c.Y, _xw(c))
@op(0x8A)
def _(c, o):
    if _w(c): c.A = c.X & 0xffff
    else: c.A = (c.A & 0xff00) | (c.X & 0xff)
    c.setnz(c.A, _w(c))
@op(0x98)
def _(c, o):
    if _w(c): c.A = c.Y & 0xffff
    else: c.A = (c.A & 0xff00) | (c.Y & 0xff)
    c.setnz(c.A, _w(c))
@op(0x9B)
def _(c, o): c.Y = c.X; c.setnz(c.Y, _xw(c))
@op(0xBB)
def _(c, o): c.X = c.Y; c.setnz(c.X, _xw(c))
@op(0x9A)
def _(c, o): c.S = c.X
@op(0xBA)
def _(c, o): c.X = c.S & (0xffff if _xw(c) else 0xff); c.setnz(c.X, _xw(c))
@op(0x5B)
def _(c, o): c.D = c.A; c.setnz(c.D, True)
@op(0x7B)
def _(c, o): c.A = c.D; c.setnz(c.A, True)
@op(0x1B)
def _(c, o): c.S = c.A
@op(0x3B)
def _(c, o): c.A = c.S; c.setnz(c.A, True)
@op(0xEB)
def _(c, o): c.A = ((c.A >> 8) | (c.A << 8)) & 0xffff; c.setnz(c.A & 0xff, False)

# stack
@op(0x48)
def _(c, o):
    if _w(c): c.push16(c.A)
    else: c.push(c.A & 0xff)
@op(0x68)
def _(c, o):
    if _w(c): c.A = c.pull16()
    else: c.A = (c.A & 0xff00) | c.pull()
    c.setnz(c.A, _w(c))
@op(0xDA)
def _(c, o):
    if _xw(c): c.push16(c.X)
    else: c.push(c.X)
@op(0xFA)
def _(c, o):
    c.X = c.pull16() if _xw(c) else c.pull(); c.setnz(c.X, _xw(c))
@op(0x5A)
def _(c, o):
    if _xw(c): c.push16(c.Y)
    else: c.push(c.Y)
@op(0x7A)
def _(c, o):
    c.Y = c.pull16() if _xw(c) else c.pull(); c.setnz(c.Y, _xw(c))
@op(0x08)
def _(c, o): c.push(c.P)
@op(0x28)
def _(c, o): c.P = c.pull(); c.fixx()
@op(0x8B)
def _(c, o): c.push(c.DB)
@op(0xAB)
def _(c, o): c.DB = c.pull(); c.setnz(c.DB, False)
@op(0x4B)
def _(c, o): c.push(c.PB)
@op(0x0B)
def _(c, o): c.push16(c.D)
@op(0x2B)
def _(c, o): c.D = c.pull16(); c.setnz(c.D, True)
@op(0xF4)
def _(c, o): c.push16(c.fetch16())
@op(0xD4)
def _(c, o): a = (c.D + c.fetch()) & 0xffff; c.push16(c.rd16(a))
@op(0x62)
def _(c, o):
    off = c.fetch16(); c.push16((c.PC + off) & 0xffff)

# loads/stores X/Y, STZ
def _ldx(c, mode, reg):
    w = _xw(c); v = c.load(mode, w); setattr(c, reg, v); c.setnz(v, w)
for code, mode in ((0xA2, 'imm'), (0xA6, 'd'), (0xB6, 'dy'), (0xAE, 'A'), (0xBE, 'Ay')):
    OPS[code] = (lambda md: lambda c, o: _ldx(c, md, 'X'))(mode)
for code, mode in ((0xA0, 'imm'), (0xA4, 'd'), (0xB4, 'dx'), (0xAC, 'A'), (0xBC, 'Ax')):
    OPS[code] = (lambda md: lambda c, o: _ldx(c, md, 'Y'))(mode)
def _stx(c, mode, reg, wflag):
    a = c.ea(mode); v = {'X': c.X, 'Y': c.Y, 'Z': 0}[reg]
    c.store(a, v, wflag(c), mode)
for code, mode in ((0x86, 'd'), (0x96, 'dy'), (0x8E, 'A')):
    OPS[code] = (lambda md: lambda c, o: _stx(c, md, 'X', _xw))(mode)
for code, mode in ((0x84, 'd'), (0x94, 'dx'), (0x8C, 'A')):
    OPS[code] = (lambda md: lambda c, o: _stx(c, md, 'Y', _xw))(mode)
for code, mode in ((0x64, 'd'), (0x74, 'dx'), (0x9C, 'A'), (0x9E, 'Ax')):
    OPS[code] = (lambda md: lambda c, o: _stx(c, md, 'Z', _w))(mode)

# compares X/Y
def _cpr(c, mode, reg):
    w = _xw(c); v = c.load(mode, w); c.cmp(getattr(c, reg), v, w)
for code, mode in ((0xE0, 'imm'), (0xE4, 'd'), (0xEC, 'A')):
    OPS[code] = (lambda md: lambda c, o: _cpr(c, md, 'X'))(mode)
for code, mode in ((0xC0, 'imm'), (0xC4, 'd'), (0xCC, 'A')):
    OPS[code] = (lambda md: lambda c, o: _cpr(c, md, 'Y'))(mode)

# inc/dec registers
def _incr(c, reg, d):
    w = _xw(c); v = (getattr(c, reg) + d) & (0xffff if w else 0xff); setattr(c, reg, v); c.setnz(v, w)
OPS[0xE8] = lambda c, o: _incr(c, 'X', 1)
OPS[0xCA] = lambda c, o: _incr(c, 'X', -1)
OPS[0xC8] = lambda c, o: _incr(c, 'Y', 1)
OPS[0x88] = lambda c, o: _incr(c, 'Y', -1)

# RMW ops
def _mk_rmw(kind):
    def f(c, mode):
        w = _w(c); mask = 0xffff if w else 0xff; sign = 0x8000 if w else 0x80
        def fn(v):
            if kind == 'INC': r = (v + 1) & mask
            elif kind == 'DEC': r = (v - 1) & mask
            elif kind == 'ASL': c.flag(1, v & sign); r = (v << 1) & mask
            elif kind == 'LSR': c.flag(1, v & 1); r = v >> 1
            elif kind == 'ROL': r = ((v << 1) | (c.P & 1)) & mask; c.flag(1, v & sign)
            elif kind == 'ROR': r = (v >> 1) | (sign if c.P & 1 else 0); c.flag(1, v & 1)
            c.setnz(r, w); return r
        c.rmw(mode, w, fn)
    return f
for kind, codes in (('ASL', {0x0A: 'acc', 0x06: 'd', 0x16: 'dx', 0x0E: 'A', 0x1E: 'Ax'}),
                    ('ROL', {0x2A: 'acc', 0x26: 'd', 0x36: 'dx', 0x2E: 'A', 0x3E: 'Ax'}),
                    ('LSR', {0x4A: 'acc', 0x46: 'd', 0x56: 'dx', 0x4E: 'A', 0x5E: 'Ax'}),
                    ('ROR', {0x6A: 'acc', 0x66: 'd', 0x76: 'dx', 0x6E: 'A', 0x7E: 'Ax'}),
                    ('INC', {0x1A: 'acc', 0xE6: 'd', 0xF6: 'dx', 0xEE: 'A', 0xFE: 'Ax'}),
                    ('DEC', {0x3A: 'acc', 0xC6: 'd', 0xD6: 'dx', 0xCE: 'A', 0xDE: 'Ax'})):
    fk = _mk_rmw(kind)
    for code, mode in codes.items():
        OPS[code] = (lambda md, fk=fk: lambda c, o: fk(c, md))(mode)

# TSB/TRB
def _tsb(c, mode, set_):
    w = _w(c)
    def fn(v):
        c.flag(2, (v & c.A & (0xffff if w else 0xff)) == 0)
        return (v | c.A) if set_ else (v & ~c.A)
    c.rmw(mode, w, fn)
OPS[0x04] = lambda c, o: _tsb(c, 'd', True)
OPS[0x0C] = lambda c, o: _tsb(c, 'A', True)
OPS[0x14] = lambda c, o: _tsb(c, 'd', False)
OPS[0x1C] = lambda c, o: _tsb(c, 'A', False)

# BIT
def _bit(c, mode):
    w = _w(c); v = c.load(mode, w)
    c.flag(2, (v & c.A & (0xffff if w else 0xff)) == 0)
    if mode != 'imm':
        sign = 0x8000 if w else 0x80
        c.flag(0x80, v & sign); c.flag(0x40, v & (sign >> 1))
for code, mode in ((0x89, 'imm'), (0x24, 'd'), (0x2C, 'A'), (0x34, 'dx'), (0x3C, 'Ax')):
    OPS[code] = (lambda md: lambda c, o: _bit(c, md))(mode)

# branches
OPS[0x10] = lambda c, o: c.branch(not c.P & 0x80)
OPS[0x30] = lambda c, o: c.branch(c.P & 0x80)
OPS[0x50] = lambda c, o: c.branch(not c.P & 0x40)
OPS[0x70] = lambda c, o: c.branch(c.P & 0x40)
OPS[0x90] = lambda c, o: c.branch(not c.P & 1)
OPS[0xB0] = lambda c, o: c.branch(c.P & 1)
OPS[0xD0] = lambda c, o: c.branch(not c.P & 2)
OPS[0xF0] = lambda c, o: c.branch(c.P & 2)
OPS[0x80] = lambda c, o: c.branch(True)
@op(0x82)
def _(c, o):
    off = c.fetch16(); c.PC = (c.PC + off) & 0xffff

# jumps
@op(0x4C)
def _(c, o): c.PC = c.fetch16()
@op(0x5C)
def _(c, o): a = c.fetch24(); c.PC = a & 0xffff; c.PB = a >> 16
@op(0x6C)
def _(c, o): a = c.fetch16(); c.PC = c.rd16(a)
@op(0x7C)
def _(c, o): a = c.fetch16(); c.PC = c.rd16((c.PB << 16) | ((a + c.X) & 0xffff))
@op(0xDC)
def _(c, o): a = c.fetch16(); t = c.rd24(a); c.PC = t & 0xffff; c.PB = t >> 16
@op(0x20)
def _(c, o): a = c.fetch16(); c.push16((c.PC - 1) & 0xffff); c.PC = a
@op(0xFC)
def _(c, o):
    a = c.fetch16(); c.push16((c.PC - 1) & 0xffff); c.PC = c.rd16((c.PB << 16) | ((a + c.X) & 0xffff))
@op(0x22)
def _(c, o):
    a = c.fetch24(); c.push(c.PB); c.push16((c.PC - 1) & 0xffff); c.PB = a >> 16; c.PC = a & 0xffff
@op(0x60)
def _(c, o): c.PC = (c.pull16() + 1) & 0xffff
@op(0x6B)
def _(c, o): c.PC = (c.pull16() + 1) & 0xffff; c.PB = c.pull()
@op(0x40)
def _(c, o):
    c.P = c.pull(); c.fixx(); c.PC = c.pull16(); c.PB = c.pull()

# block moves
def _mv(c, dirn):
    dst = c.fetch(); src = c.fetch()
    c.DB = dst
    while True:
        c.wr(dst << 16 | c.Y, c.rd(src << 16 | c.X))
        mask = 0xffff if _xw(c) else 0xff
        c.X = (c.X + dirn) & mask; c.Y = (c.Y + dirn) & mask
        c.A = (c.A - 1) & 0xffff
        if c.A == 0xffff: break
OPS[0x54] = lambda c, o: _mv(c, 1)
OPS[0x44] = lambda c, o: _mv(c, -1)

@op(0xEA)
def _(c, o): pass
@op(0x42)
def _(c, o): c.fetch()
@op(0xCB)
def _(c, o): raise Halt('WAI')
@op(0xDB)
def _(c, o): raise Halt('STP')
@op(0x00, 0x02)
def _(c, o): raise Halt('BRK/COP at %02X:%04X' % (c.PB, c.PC))
