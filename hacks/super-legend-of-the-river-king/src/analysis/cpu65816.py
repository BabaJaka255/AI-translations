"""Minimal 65816 interpreter, just enough to run KNT2's text routines for patch testing.
LoROM map. Not cycle accurate. Unknown opcodes raise."""
import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys
sys.path.insert(0,P.ANALYSIS)
import dis as _dis

OPS = _dis.ops
LEN = _dis.LEN


class CPU:
    def __init__(self, rom, wram=None):
        self.rom = bytearray(rom)
        self.wram = bytearray(wram if wram is not None else 0x20000)
        self.A = 0; self.X = 0; self.Y = 0; self.S = 0x1FFF; self.D = 0; self.DB = 0; self.PB = 0x82; self.PC = 0
        self.N = self.V = self.Z = self.C = self.I = self.Dm = 0
        self.m = 1; self.x = 1  # 8-bit flags (1 = 8 bit)
        self.hooks = {}   # (bank,pc) -> python callable(cpu) emulating a whole routine (then RTL/RTS done by hook)
        self.steps = 0
        self.log = []
        self.vram_dma = []

    # ---- memory
    def rd(self, bank, addr):
        bank &= 0xFF; addr &= 0xFFFF
        if bank in (0x7E, 0x7F):
            return self.wram[((bank & 1) << 16) | addr]
        b = bank & 0x7F
        if b < 0x40:
            if addr < 0x2000:
                return self.wram[addr]
            if addr < 0x8000:
                return 0
            off = (b << 15) | (addr & 0x7FFF)
            return self.rom[off] if off < len(self.rom) else 0xFF
        if bank >= 0x80:
            off = ((bank & 0x7F) << 15) | (addr & 0x7FFF)
            if addr >= 0x8000:
                return self.rom[off] if off < len(self.rom) else 0xFF
        return 0

    def wr(self, bank, addr, v):
        bank &= 0xFF; addr &= 0xFFFF; v &= 0xFF
        if bank in (0x7E, 0x7F):
            self.wram[((bank & 1) << 16) | addr] = v
        elif (bank & 0x7F) < 0x40 and addr < 0x2000:
            self.wram[addr] = v
        # everything else ignored (registers, ROM)

    def rd16(self, bank, addr):
        return self.rd(bank, addr) | (self.rd(bank, addr + 1) << 8)

    def wr16(self, bank, addr, v):
        self.wr(bank, addr, v & 0xFF); self.wr(bank, addr + 1, (v >> 8) & 0xFF)

    def rd24(self, bank, addr):
        return self.rd16(bank, addr) | (self.rd(bank, addr + 2) << 16)

    # ---- stack
    def push(self, v):
        self.wr(0, self.S, v); self.S = (self.S - 1) & 0xFFFF

    def pull(self):
        self.S = (self.S + 1) & 0xFFFF; return self.rd(0, self.S)

    def push16(self, v):
        self.push((v >> 8) & 0xFF); self.push(v & 0xFF)

    def pull16(self):
        lo = self.pull(); return lo | (self.pull() << 8)

    # ---- flags
    def P(self):
        return (self.N << 7) | (self.V << 6) | (self.m << 5) | (self.x << 4) | (self.Dm << 3) | (self.I << 2) | (self.Z << 1) | self.C

    def setP(self, p):
        self.N = (p >> 7) & 1; self.V = (p >> 6) & 1; self.m = (p >> 5) & 1; self.x = (p >> 4) & 1
        self.Dm = (p >> 3) & 1; self.I = (p >> 2) & 1; self.Z = (p >> 1) & 1; self.C = p & 1
        if self.x:
            self.X &= 0xFF; self.Y &= 0xFF

    def nz(self, v, eight):
        if eight:
            self.N = (v >> 7) & 1; self.Z = int((v & 0xFF) == 0)
        else:
            self.N = (v >> 15) & 1; self.Z = int((v & 0xFFFF) == 0)

    # ---- operand fetch
    def fetch(self, n):
        v = 0
        for i in range(n):
            v |= self.rd(self.PB, self.PC + i) << (8 * i)
        self.PC = (self.PC + n) & 0xFFFF
        return v

    def ea(self, mode, v):
        """returns (bank, addr) of operand for memory modes"""
        D = self.D
        if mode == 'd': return 0, (D + v) & 0xFFFF
        if mode == 'dx': return 0, (D + v + self.X) & 0xFFFF
        if mode == 'dy': return 0, (D + v + self.Y) & 0xFFFF
        if mode == 'A': return self.DB, v
        if mode == 'Ax': a = v + self.X; return (self.DB + (a >> 16)) & 0xFF, a & 0xFFFF
        if mode == 'Ay': a = v + self.Y; return (self.DB + (a >> 16)) & 0xFF, a & 0xFFFF
        if mode == 'L': return v >> 16, v & 0xFFFF
        if mode == 'Lx': a = v + self.X; return (a >> 16) & 0xFF, a & 0xFFFF
        if mode == '(d)':
            p = self.rd16(0, (D + v) & 0xFFFF); return self.DB, p
        if mode == '(d,x)':
            p = self.rd16(0, (D + v + self.X) & 0xFFFF); return self.DB, p
        if mode == '(d),y':
            p = self.rd16(0, (D + v) & 0xFFFF) + self.Y; return (self.DB + (p >> 16)) & 0xFF, p & 0xFFFF
        if mode == '[d]':
            a = self.rd24(0, (D + v) & 0xFFFF); return a >> 16, a & 0xFFFF
        if mode == '[d],y':
            a = self.rd24(0, (D + v) & 0xFFFF) + self.Y; return (a >> 16) & 0xFF, a & 0xFFFF
        if mode == 's': return 0, (self.S + v) & 0xFFFF
        if mode == '(s),y':
            p = self.rd16(0, (self.S + v) & 0xFFFF) + self.Y; return (self.DB + (p >> 16)) & 0xFF, p & 0xFFFF
        raise Exception('mode ' + mode)

    def step(self):
        pc0 = (self.PB, self.PC)
        if pc0 in self.hooks:
            self.hooks[pc0](self); return
        op = self.rd(self.PB, self.PC)
        if op not in OPS:
            raise Exception('bad opcode %02X at %02X:%04X' % (op, self.PB, self.PC))
        mn, mode = OPS[op]
        self.PC = (self.PC + 1) & 0xFFFF
        if mode == 'M': ln = 1 if self.m else 2
        elif mode == 'X': ln = 1 if self.x else 2
        else: ln = LEN[mode] - 1
        v = self.fetch(ln) if ln else 0
        self.steps += 1
        getattr(self, 'op_' + mn)(mode, v)

    # ---- helpers
    def val(self, mode, v, eight):
        if mode in ('M', 'X', '1'):
            return v
        b, a = self.ea(mode, v)
        return self.rd(b, a) if eight else self.rd16(b, a)

    def store(self, mode, v, val, eight):
        b, a = self.ea(mode, v)
        if eight: self.wr(b, a, val)
        else: self.wr16(b, a, val)

    # loads/stores
    def op_LDA(self, mode, v):
        e = self.m; r = self.val(mode, v, e)
        self.A = (self.A & 0xFF00) | r if e else r; self.nz(r, e)

    def op_LDX(self, mode, v):
        e = self.x; r = self.val(mode, v, e); self.X = r; self.nz(r, e)

    def op_LDY(self, mode, v):
        e = self.x; r = self.val(mode, v, e); self.Y = r; self.nz(r, e)

    def op_STA(self, mode, v):
        e = self.m; self.store(mode, v, self.A & (0xFF if e else 0xFFFF), e)

    def op_STX(self, mode, v):
        e = self.x; self.store(mode, v, self.X, e)

    def op_STY(self, mode, v):
        e = self.x; self.store(mode, v, self.Y, e)

    def op_STZ(self, mode, v):
        self.store(mode, v, 0, self.m)

    # ALU
    def _acc(self, f):
        e = self.m; return f, e

    def op_ORA(self, mode, v):
        e = self.m; r = self.val(mode, v, e)
        self.A = (self.A & 0xFF00) | ((self.A | r) & 0xFF) if e else (self.A | r) & 0xFFFF
        self.nz(self.A, e)

    def op_AND(self, mode, v):
        e = self.m; r = self.val(mode, v, e)
        self.A = (self.A & 0xFF00) | ((self.A & r) & 0xFF) if e else (self.A & r) & 0xFFFF
        self.nz(self.A, e)

    def op_EOR(self, mode, v):
        e = self.m; r = self.val(mode, v, e)
        self.A = (self.A & 0xFF00) | ((self.A ^ r) & 0xFF) if e else (self.A ^ r) & 0xFFFF
        self.nz(self.A, e)

    def op_ADC(self, mode, v):
        e = self.m; r = self.val(mode, v, e); mask = 0xFF if e else 0xFFFF; a = self.A & mask
        t = a + r + self.C
        self.V = int(((~(a ^ r) & (a ^ t)) & (0x80 if e else 0x8000)) != 0)
        self.C = int(t > mask); t &= mask
        self.A = (self.A & 0xFF00) | t if e else t; self.nz(t, e)

    def op_SBC(self, mode, v):
        e = self.m; r = self.val(mode, v, e); mask = 0xFF if e else 0xFFFF; a = self.A & mask
        r2 = (~r) & mask; t = a + r2 + self.C
        self.V = int(((~(a ^ r2) & (a ^ t)) & (0x80 if e else 0x8000)) != 0)
        self.C = int(t > mask); t &= mask
        self.A = (self.A & 0xFF00) | t if e else t; self.nz(t, e)

    def _cmp(self, reg, mode, v, e):
        r = self.val(mode, v, e); mask = 0xFF if e else 0xFFFF
        t = (reg & mask) - r; self.C = int(t >= 0); self.nz(t & mask, e)

    def op_CMP(self, mode, v): self._cmp(self.A, mode, v, self.m)
    def op_CPX(self, mode, v): self._cmp(self.X, mode, v, self.x)
    def op_CPY(self, mode, v): self._cmp(self.Y, mode, v, self.x)

    def op_BIT(self, mode, v):
        e = self.m; r = self.val(mode, v, e); mask = 0xFF if e else 0xFFFF
        self.Z = int((self.A & r & mask) == 0)
        if mode != 'M':
            self.N = (r >> (7 if e else 15)) & 1; self.V = (r >> (6 if e else 14)) & 1

    # RMW
    def _rmw(self, mode, v, f):
        if mode == 'a':
            e = self.m; mask = 0xFF if e else 0xFFFF
            r = f(self.A & mask, e) & mask
            self.A = (self.A & 0xFF00) | r if e else r; self.nz(r, e)
        else:
            e = self.m; b, a = self.ea(mode, v)
            cur = self.rd(b, a) if e else self.rd16(b, a)
            r = f(cur, e) & (0xFF if e else 0xFFFF)
            if e: self.wr(b, a, r)
            else: self.wr16(b, a, r)
            self.nz(r, e)

    def op_ASL(self, mode, v):
        def f(x, e): self.C = (x >> (7 if e else 15)) & 1; return x << 1
        self._rmw(mode, v, f)

    def op_LSR(self, mode, v):
        def f(x, e): self.C = x & 1; return x >> 1
        self._rmw(mode, v, f)

    def op_ROL(self, mode, v):
        def f(x, e):
            c = self.C; self.C = (x >> (7 if e else 15)) & 1; return (x << 1) | c
        self._rmw(mode, v, f)

    def op_ROR(self, mode, v):
        def f(x, e):
            c = self.C; self.C = x & 1; return (x >> 1) | (c << (7 if e else 15))
        self._rmw(mode, v, f)

    def op_INC(self, mode, v): self._rmw(mode, v, lambda x, e: x + 1)
    def op_DEC(self, mode, v): self._rmw(mode, v, lambda x, e: x - 1)

    def op_TSB(self, mode, v):
        e = self.m; b, a = self.ea(mode, v); cur = self.rd(b, a) if e else self.rd16(b, a)
        self.Z = int((cur & self.A) == 0); n = cur | self.A
        self.wr(b, a, n) if e else self.wr16(b, a, n)

    def op_TRB(self, mode, v):
        e = self.m; b, a = self.ea(mode, v); cur = self.rd(b, a) if e else self.rd16(b, a)
        self.Z = int((cur & self.A) == 0); n = cur & ~self.A
        self.wr(b, a, n) if e else self.wr16(b, a, n)

    # index inc/dec, transfers
    def op_INX(self, m, v): self.X = (self.X + 1) & (0xFF if self.x else 0xFFFF); self.nz(self.X, self.x)
    def op_INY(self, m, v): self.Y = (self.Y + 1) & (0xFF if self.x else 0xFFFF); self.nz(self.Y, self.x)
    def op_DEX(self, m, v): self.X = (self.X - 1) & (0xFF if self.x else 0xFFFF); self.nz(self.X, self.x)
    def op_DEY(self, m, v): self.Y = (self.Y - 1) & (0xFF if self.x else 0xFFFF); self.nz(self.Y, self.x)

    def op_TAX(self, m, v): self.X = self.A & (0xFF if self.x else 0xFFFF); self.nz(self.X, self.x)
    def op_TAY(self, m, v): self.Y = self.A & (0xFF if self.x else 0xFFFF); self.nz(self.Y, self.x)
    def op_TXA(self, m, v):
        r = self.X & (0xFF if self.m else 0xFFFF)
        self.A = (self.A & 0xFF00) | r if self.m else r; self.nz(r, self.m)
    def op_TYA(self, m, v):
        r = self.Y & (0xFF if self.m else 0xFFFF)
        self.A = (self.A & 0xFF00) | r if self.m else r; self.nz(r, self.m)
    def op_TXY(self, m, v): self.Y = self.X; self.nz(self.Y, self.x)
    def op_TYX(self, m, v): self.X = self.Y; self.nz(self.X, self.x)
    def op_TCS(self, m, v): self.S = self.A
    def op_TSC(self, m, v): self.A = self.S; self.nz(self.A, 0)
    def op_TCD(self, m, v): self.D = self.A; self.nz(self.A, 0)
    def op_TDC(self, m, v): self.A = self.D; self.nz(self.A, 0)
    def op_TXS(self, m, v): self.S = self.X
    def op_TSX(self, m, v): self.X = self.S & (0xFF if self.x else 0xFFFF); self.nz(self.X, self.x)
    def op_XBA(self, m, v):
        self.A = ((self.A & 0xFF) << 8) | (self.A >> 8); self.nz(self.A & 0xFF, 1)

    # flags
    def op_CLC(self, m, v): self.C = 0
    def op_SEC(self, m, v): self.C = 1
    def op_CLI(self, m, v): self.I = 0
    def op_SEI(self, m, v): self.I = 1
    def op_CLD(self, m, v): self.Dm = 0
    def op_SED(self, m, v): self.Dm = 1
    def op_CLV(self, m, v): self.V = 0
    def op_NOP(self, m, v): pass
    def op_REP(self, m, v): self.setP(self.P() & ~v)
    def op_SEP(self, m, v): self.setP(self.P() | v)
    def op_XCE(self, m, v): pass

    # stack ops
    def op_PHA(self, m, v):
        if self.m: self.push(self.A & 0xFF)
        else: self.push16(self.A)
    def op_PLA(self, m, v):
        if self.m:
            r = self.pull(); self.A = (self.A & 0xFF00) | r; self.nz(r, 1)
        else:
            self.A = self.pull16(); self.nz(self.A, 0)
    def op_PHX(self, m, v):
        if self.x: self.push(self.X)
        else: self.push16(self.X)
    def op_PLX(self, m, v):
        if self.x: self.X = self.pull()
        else: self.X = self.pull16()
        self.nz(self.X, self.x)
    def op_PHY(self, m, v):
        if self.x: self.push(self.Y)
        else: self.push16(self.Y)
    def op_PLY(self, m, v):
        if self.x: self.Y = self.pull()
        else: self.Y = self.pull16()
        self.nz(self.Y, self.x)
    def op_PHP(self, m, v): self.push(self.P())
    def op_PLP(self, m, v): self.setP(self.pull())
    def op_PHB(self, m, v): self.push(self.DB)
    def op_PLB(self, m, v): self.DB = self.pull(); self.nz(self.DB, 1)
    def op_PHD(self, m, v): self.push16(self.D)
    def op_PLD(self, m, v): self.D = self.pull16(); self.nz(self.D, 0)
    def op_PHK(self, m, v): self.push(self.PB)
    def op_PEA(self, m, v): self.push16(v)

    # control
    def _br(self, cond, v):
        if cond:
            d = v - 256 if v > 127 else v
            self.PC = (self.PC + d) & 0xFFFF

    def op_BRA(self, m, v): self._br(True, v)
    def op_BEQ(self, m, v): self._br(self.Z, v)
    def op_BNE(self, m, v): self._br(not self.Z, v)
    def op_BCC(self, m, v): self._br(not self.C, v)
    def op_BCS(self, m, v): self._br(self.C, v)
    def op_BPL(self, m, v): self._br(not self.N, v)
    def op_BMI(self, m, v): self._br(self.N, v)
    def op_BVC(self, m, v): self._br(not self.V, v)
    def op_BVS(self, m, v): self._br(self.V, v)
    def op_BRL(self, m, v):
        d = v - 65536 if v > 32767 else v; self.PC = (self.PC + d) & 0xFFFF

    def op_JMP(self, mode, v):
        if mode == 'A': self.PC = v
        elif mode == '(A)': self.PC = self.rd16(0, v)
        elif mode == '(A,x)': self.PC = self.rd16(self.PB, (v + self.X) & 0xFFFF)
        else: raise Exception('jmp mode')

    def op_JML(self, mode, v):
        if mode == 'L': self.PB = v >> 16; self.PC = v & 0xFFFF
        else:
            a = self.rd24(0, v); self.PB = a >> 16; self.PC = a & 0xFFFF

    def op_JSR(self, mode, v):
        self.push16((self.PC - 1) & 0xFFFF)
        if mode == 'A': self.PC = v
        else: self.PC = self.rd16(self.PB, (v + self.X) & 0xFFFF)

    def op_JSL(self, mode, v):
        self.push(self.PB); self.push16((self.PC - 1) & 0xFFFF)
        self.PB = v >> 16; self.PC = v & 0xFFFF

    def op_RTS(self, m, v): self.PC = (self.pull16() + 1) & 0xFFFF
    def op_RTL(self, m, v):
        self.PC = (self.pull16() + 1) & 0xFFFF; self.PB = self.pull()

    def op_MVN(self, mode, v):
        # operand bytes: dst, src (as encoded: first byte=dst, second=src)
        dst = v & 0xFF; src = v >> 8
        while True:
            self.wr(dst, self.Y, self.rd(src, self.X))
            self.X = (self.X + 1) & 0xFFFF; self.Y = (self.Y + 1) & 0xFFFF
            self.A = (self.A - 1) & 0xFFFF
            if self.A == 0xFFFF: break
        self.DB = dst

    def op_MVP(self, mode, v):
        dst = v & 0xFF; src = v >> 8
        while True:
            self.wr(dst, self.Y, self.rd(src, self.X))
            self.X = (self.X - 1) & 0xFFFF; self.Y = (self.Y - 1) & 0xFFFF
            self.A = (self.A - 1) & 0xFFFF
            if self.A == 0xFFFF: break
        self.DB = dst

    # ---- run helper
    def call(self, bank, addr, max_steps=2_000_000, long_return=False):
        """run a JSR-style routine until its RTS returns (sentinel return address)"""
        SENT = 0xFFF0
        if long_return:
            self.push(0xFE); self.push16(SENT - 1)
        else:
            self.push16(SENT - 1)
        self.PB = bank; self.PC = addr
        n = 0
        while True:
            if (long_return and self.PB == 0xFE and self.PC == SENT) or (not long_return and self.PB == bank and self.PC == SENT):
                return
            self.step(); n += 1
            if n > max_steps:
                raise Exception('step limit; at %02X:%04X' % (self.PB, self.PC))
