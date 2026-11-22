"""HuC6280 interpreter for tracing from a Beetle PCE Fast savestate.

    m = Machine.from_state('x.st', 'sys/syscard3.pce')
    m.pad = 0x08                     # buttons held (bit: 0 I, 1 II, 2 SEL, 3 RUN, 4 UP, 5 RIGHT, 6 DOWN, 7 LEFT)
    m.run(200000, vsync_every=30000)
Hooks: m.on_read(phys, pc), m.on_vram_write(addr, value, pc), m.on_exec(pc) (set to functions).
Not cycle accurate: VDC/VCE/PSG/timer are stubs, CD ports return 0."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mdfnstate import parse
from dis6280 import T as OPT

C, Z, I, D, B, T, V, N = 1, 2, 4, 8, 16, 32, 64, 128

class Machine:
    def __init__(s):
        s.mem = {}            # bank -> bytearray(8192)
        s.mpr = [0xFF, 0xF8, 0, 0, 0, 0, 0, 0]
        s.a = s.x = s.y = 0; s.s = 0xFF; s.p = I; s.pc = 0
        s.vram = bytearray(65536); s.vreg = 0; s.mawr = 0; s.marr = 0; s.vlatch = 0; s.vstatus = 0
        s.cr = 0; s.mwr = 0
        s.pad = 0; s.padsel = 0
        s.irq_disable = 0; s.irq_pending = 0
        s.on_read = None; s.on_vram_write = None; s.on_exec = None; s.on_write = None
        s.steps = 0; s.rom_banks = set()
    @classmethod
    def from_state(cls, path, bios):
        st = parse(open(path, 'rb').read()); m = cls()
        rom = open(bios, 'rb').read()
        for b in range(len(rom) // 8192): m.mem[b] = bytearray(rom[b * 8192:(b + 1) * 8192]); m.rom_banks.add(b)
        m.mem[0xF8] = bytearray(st['MAIN']['BaseRAM'][1])
        cd = st['HuC']['ROMSpace + 0x68 * 8192'][1]
        for i in range(len(cd) // 8192): m.mem[0x68 + i] = bytearray(cd[i * 8192:(i + 1) * 8192])
        c = st['CPU']
        m.pc = int.from_bytes(c['PC'][1], 'little'); m.a = c['A'][1][0]; m.x = c['X'][1][0]; m.y = c['Y'][1][0]
        m.s = c['S'][1][0]; m.p = c['P'][1][0]; m.mpr = list(c['MPR'][1])
        m.irq_disable = (~c['IRQMask'][1][0]) & 7   # Mednafen stores the enabled mask
        v = st['VDC0']
        m.vram = bytearray(v['VRAM'][1]); m.vreg = v['select'][1][0]
        m.mawr = int.from_bytes(v['MAWR'][1], 'little'); m.marr = int.from_bytes(v['MARR'][1], 'little')
        m.cr = int.from_bytes(v['CR'][1], 'little'); m.mwr = int.from_bytes(v['MWR'][1], 'little')
        return m
    # ---- memory ----
    def phys(s, addr): return s.mpr[addr >> 13] * 8192 + (addr & 0x1FFF)
    def rd(s, addr):
        bank = s.mpr[addr >> 13]; off = addr & 0x1FFF
        if bank == 0xFF: return s.io_read(off)
        if bank in (0xF9, 0xFA, 0xFB): bank = 0xF8
        if s.on_read: s.on_read(bank * 8192 + off, s.pc)
        m = s.mem.get(bank)
        return m[off] if m is not None else 0xFF
    def wr(s, addr, v):
        bank = s.mpr[addr >> 13]; off = addr & 0x1FFF
        if bank == 0xFF: return s.io_write(off, v)
        if bank in (0xF9, 0xFA, 0xFB): bank = 0xF8
        if bank in s.rom_banks: return
        if s.on_write: s.on_write(bank * 8192 + off, v, s.pc)
        m = s.mem.get(bank)
        if m is None: m = s.mem[bank] = bytearray(8192)
        m[off] = v
    def zp(s, a): return s.mem[0xF8][a & 0xFF]
    def zpw(s, a, v): s.mem[0xF8][a & 0xFF] = v
    def zp16(s, a): return s.zp(a) | s.zp(a + 1) << 8
    def rd16(s, a): return s.rd(a) | s.rd((a + 1) & 0xFFFF) << 8
    # ---- I/O ----
    def io_read(s, off):
        if off < 0x400:
            r = off & 3
            if r == 0: v = s.vstatus; s.vstatus = 0; s.irq_pending &= ~1; return v
            if r == 2: return s.vram[(s.marr * 2) & 0xFFFF]
            if r == 3:
                v = s.vram[(s.marr * 2 + 1) & 0xFFFF]; s.marr = (s.marr + s.inc()) & 0xFFFF; return v
            return 0
        if 0x1000 <= off < 0x1400:
            p = (~s.pad) & 0xFF
            nib = (p >> 4) if s.padsel else (p & 15)
            return 0xB0 | nib
        if 0x1400 <= off < 0x1800:
            if (off & 3) == 2: return s.irq_disable
            if (off & 3) == 3: return s.irq_pending
            return 0
        return 0
    def inc(s): return (1, 32, 64, 128)[(s.cr >> 11) & 3]
    def io_write(s, off, v):
        if off < 0x400:
            r = off & 3
            if r == 0: s.vreg = v & 0x1F
            elif r == 2: s.vlatch = v; s.setreg(False, v)
            elif r == 3: s.setreg(True, v)
        elif 0x1000 <= off < 0x1400: s.padsel = v & 1
        elif 0x1400 <= off < 0x1800:
            if (off & 3) == 2: s.irq_disable = v
    def setreg(s, hi, v):
        r = s.vreg
        if r == 0:
            s.mawr = (s.mawr & 0xFF) | v << 8 if hi else (s.mawr & 0xFF00) | v
        elif r == 1:
            s.marr = (s.marr & 0xFF) | v << 8 if hi else (s.marr & 0xFF00) | v
        elif r == 2:
            if hi:
                a = s.mawr & 0x7FFF
                s.vram[a * 2] = s.vlatch; s.vram[a * 2 + 1] = v
                if s.on_vram_write: s.on_vram_write(a, s.vlatch | v << 8, s.pc)
                s.mawr = (s.mawr + s.inc()) & 0xFFFF
        elif r == 5:
            s.cr = (s.cr & 0xFF) | v << 8 if hi else (s.cr & 0xFF00) | v
        elif r == 9:
            s.mwr = (s.mwr & 0xFF) | v << 8 if hi else (s.mwr & 0xFF00) | v
    # ---- stack / flags ----
    def push(s, v): s.mem[0xF8][0x100 + s.s] = v & 0xFF; s.s = (s.s - 1) & 0xFF
    def pull(s): s.s = (s.s + 1) & 0xFF; return s.mem[0xF8][0x100 + s.s]
    def nz(s, v):
        v &= 0xFF; s.p = (s.p & ~(N | Z)) | (v & N) | (Z if v == 0 else 0); return v
    def flag(s, f, on): s.p = (s.p | f) if on else (s.p & ~f)
    def irq(s, vec):
        s.push(s.pc >> 8); s.push(s.pc); s.push(s.p & ~B); s.p = (s.p | I) & ~(D | T)
        s.pc = s.rd16(vec)
    # ---- run ----
    def run(s, n, vsync_every=0):
        for _ in range(n):
            s.steps += 1
            if vsync_every and s.steps % vsync_every == 0:
                s.vstatus |= 0x20; s.irq_pending |= 2
                if not (s.p & I) and not (s.irq_disable & 2): s.irq(0xFFF8)
            if s.on_exec: s.on_exec(s.pc)
            s.step()
    def addr_mode(s, mode):
        pc = s.pc
        if mode == 'zp': a = 0x2000 | s.rd(pc); s.pc += 1; return a
        if mode == 'zpx': a = 0x2000 | ((s.rd(pc) + s.x) & 0xFF); s.pc += 1; return a
        if mode == 'zpy': a = 0x2000 | ((s.rd(pc) + s.y) & 0xFF); s.pc += 1; return a
        if mode == 'abs': a = s.rd16(pc); s.pc += 2; return a
        if mode == 'abx': a = (s.rd16(pc) + s.x) & 0xFFFF; s.pc += 2; return a
        if mode == 'aby': a = (s.rd16(pc) + s.y) & 0xFFFF; s.pc += 2; return a
        if mode == 'izx': z = (s.rd(pc) + s.x) & 0xFF; s.pc += 1; return s.zp16(z)
        if mode == 'izy': z = s.rd(pc); s.pc += 1; return (s.zp16(z) + s.y) & 0xFFFF
        if mode == 'izp': z = s.rd(pc); s.pc += 1; return s.zp16(z)
        raise ValueError(mode)
    def adc(s, v):
        c = s.p & C
        if s.p & D:
            lo = (s.a & 15) + (v & 15) + c
            hi = (s.a >> 4) + (v >> 4)
            if lo > 9: lo -= 10; hi += 1
            cc = hi > 9
            if cc: hi -= 10
            s.flag(C, cc); s.a = s.nz((hi << 4) | lo)
        else:
            r = s.a + v + c
            s.flag(V, (~(s.a ^ v) & (s.a ^ r) & 0x80) != 0); s.flag(C, r > 0xFF); s.a = s.nz(r)
    def sbc(s, v):
        if s.p & D:
            c = 1 - (s.p & C)
            lo = (s.a & 15) - (v & 15) - c; hi = (s.a >> 4) - (v >> 4)
            if lo < 0: lo += 10; hi -= 1
            cc = hi >= 0
            if not cc: hi += 10
            s.flag(C, cc); s.a = s.nz((hi << 4) | lo)
        else:
            s.adc(v ^ 0xFF)
    def cmp(s, r, v): t = r - v; s.flag(C, t >= 0); s.nz(t)
    def branch(s, cond):
        o = s.rd(s.pc); s.pc += 1
        if cond: s.pc = (s.pc + (o ^ 0x80) - 0x80) & 0xFFFF
    def step(s):
        pc0 = s.pc; op = s.rd(s.pc); s.pc = (s.pc + 1) & 0xFFFF
        name, mode = OPT.get(op, ('???', 'imp'))
        t_flag = s.p & T; s.p &= ~T
        if name in ('lda', 'ldx', 'ldy', 'ora', 'and', 'eor', 'adc', 'sbc', 'cmp', 'cpx', 'cpy', 'bit'):
            if mode == 'imm': v = s.rd(s.pc); s.pc += 1
            else: v = s.rd(s.addr_mode(mode))
            if name == 'lda': s.a = s.nz(v)
            elif name == 'ldx': s.x = s.nz(v)
            elif name == 'ldy': s.y = s.nz(v)
            elif name in ('ora', 'and', 'eor'):
                if t_flag:
                    za = 0x2000 | s.x; m = s.rd(za)
                    r = m | v if name == 'ora' else (m & v if name == 'and' else m ^ v)
                    s.wr(za, s.nz(r))
                else:
                    s.a = s.nz(s.a | v if name == 'ora' else (s.a & v if name == 'and' else s.a ^ v))
            elif name == 'adc': s.adc(v)
            elif name == 'sbc': s.sbc(v)
            elif name == 'cmp': s.cmp(s.a, v)
            elif name == 'cpx': s.cmp(s.x, v)
            elif name == 'cpy': s.cmp(s.y, v)
            elif name == 'bit':
                s.flag(Z, (s.a & v) == 0)
                if mode != 'imm': s.p = (s.p & ~(N | V)) | (v & (N | V))
            return
        if name in ('sta', 'stx', 'sty', 'stz'):
            a = s.addr_mode(mode)
            s.wr(a, {'sta': s.a, 'stx': s.x, 'sty': s.y, 'stz': 0}[name]); return
        if name in ('asl', 'lsr', 'rol', 'ror', 'inc', 'dec'):
            if mode == 'acc': v = s.a
            else: a = s.addr_mode(mode); v = s.rd(a)
            if name == 'asl': s.flag(C, v & 0x80); v = (v << 1) & 0xFF
            elif name == 'lsr': s.flag(C, v & 1); v >>= 1
            elif name == 'rol': c = s.p & C; s.flag(C, v & 0x80); v = ((v << 1) | c) & 0xFF
            elif name == 'ror': c = s.p & C; s.flag(C, v & 1); v = (v >> 1) | (c << 7)
            elif name == 'inc': v = (v + 1) & 0xFF
            else: v = (v - 1) & 0xFF
            s.nz(v)
            if mode == 'acc': s.a = v
            else: s.wr(a, v)
            return
        if mode == 'rel':
            f = s.p
            cond = {'bpl': not f & N, 'bmi': f & N, 'bvc': not f & V, 'bvs': f & V, 'bcc': not f & C, 'bcs': f & C,
                    'bne': not f & Z, 'beq': f & Z, 'bra': True, 'bsr': True}[name]
            if name == 'bsr':
                ret = (s.pc) & 0xFFFF; s.push(ret >> 8); s.push(ret)  # pc points at offset byte
            s.branch(cond); return
        if mode == 'zrel':
            z = s.rd(s.pc); s.pc += 1; v = s.zp(z); bit = int(name[3])
            s.branch(((v >> bit) & 1) == (1 if name.startswith('bbs') else 0)); return
        if name.startswith('rmb') or name.startswith('smb'):
            z = s.rd(s.pc); s.pc += 1; bit = int(name[3]); v = s.zp(z)
            s.zpw(z, v | (1 << bit) if name.startswith('smb') else v & ~(1 << bit)); return
        if name == 'jmp':
            if mode == 'abs': s.pc = s.rd16(s.pc)
            elif mode == 'ind': s.pc = s.rd16(s.rd16(s.pc))
            else: s.pc = s.rd16((s.rd16(s.pc) + s.x) & 0xFFFF)
            return
        if name == 'jsr':
            t = s.rd16(s.pc); ret = (s.pc + 1) & 0xFFFF; s.push(ret >> 8); s.push(ret); s.pc = t; return
        if name == 'rts': lo = s.pull(); hi = s.pull(); s.pc = ((hi << 8 | lo) + 1) & 0xFFFF; return
        if name == 'rti': s.p = s.pull(); lo = s.pull(); hi = s.pull(); s.pc = hi << 8 | lo; return
        if name in ('tsb', 'trb'):
            a = s.addr_mode(mode); v = s.rd(a)
            s.flag(Z, (v & s.a) == 0); s.p = (s.p & ~(N | V)) | (v & (N | V))
            s.wr(a, v | s.a if name == 'tsb' else v & ~s.a); return
        if name == 'tst':
            imm = s.rd(s.pc); s.pc += 1
            m2 = {'tst_zp': 'zp', 'tst_abs': 'abs', 'tst_zpx': 'zpx', 'tst_abx': 'abx'}[mode]
            v = s.rd(s.addr_mode(m2)); s.flag(Z, (v & imm) == 0); s.p = (s.p & ~(N | V)) | (v & (N | V)); return
        if name in ('tam', 'tma'):
            m = s.rd(s.pc); s.pc += 1
            for i in range(8):
                if m >> i & 1:
                    if name == 'tam': s.mpr[i] = s.a
                    else: s.a = s.mpr[i]
            return
        if name in ('st0', 'st1', 'st2'):
            v = s.rd(s.pc); s.pc += 1
            s.io_write({'st0': 0, 'st1': 2, 'st2': 3}[name], v); return
        if mode == 'blk':
            src = s.rd16(s.pc); dst = s.rd16(s.pc + 2); ln = s.rd16(s.pc + 4) or 0x10000; s.pc += 6
            alt = 0
            for i in range(ln):
                s.wr(dst, s.rd(src))
                if name == 'tii': src += 1; dst += 1
                elif name == 'tdd': src -= 1; dst -= 1
                elif name == 'tin': src += 1
                elif name == 'tia': src += 1; dst += (1 if alt == 0 else -1); alt ^= 1
                elif name == 'tai': dst += 1; src += (1 if alt == 0 else -1); alt ^= 1
                src &= 0xFFFF; dst &= 0xFFFF
            return
        f = {
            'clc': lambda: s.flag(C, 0), 'sec': lambda: s.flag(C, 1), 'cli': lambda: s.flag(I, 0), 'sei': lambda: s.flag(I, 1),
            'cld': lambda: s.flag(D, 0), 'sed': lambda: s.flag(D, 1), 'clv': lambda: s.flag(V, 0), 'set': lambda: s.flag(T, 1),
            'nop': lambda: None, 'csh': lambda: None, 'csl': lambda: None,
        }
        if name in f: f[name](); return
        if name == 'tax': s.x = s.nz(s.a)
        elif name == 'tay': s.y = s.nz(s.a)
        elif name == 'txa': s.a = s.nz(s.x)
        elif name == 'tya': s.a = s.nz(s.y)
        elif name == 'tsx': s.x = s.nz(s.s)
        elif name == 'txs': s.s = s.x
        elif name == 'inx': s.x = s.nz(s.x + 1)
        elif name == 'iny': s.y = s.nz(s.y + 1)
        elif name == 'dex': s.x = s.nz(s.x - 1)
        elif name == 'dey': s.y = s.nz(s.y - 1)
        elif name == 'pha': s.push(s.a)
        elif name == 'phx': s.push(s.x)
        elif name == 'phy': s.push(s.y)
        elif name == 'php': s.push(s.p | B)
        elif name == 'pla': s.a = s.nz(s.pull())
        elif name == 'plx': s.x = s.nz(s.pull())
        elif name == 'ply': s.y = s.nz(s.pull())
        elif name == 'plp': s.p = s.pull()
        elif name == 'cla': s.a = 0
        elif name == 'clx': s.x = 0
        elif name == 'cly': s.y = 0
        elif name == 'sax': s.a, s.x = s.x, s.a
        elif name == 'say': s.a, s.y = s.y, s.a
        elif name == 'sxy': s.x, s.y = s.y, s.x
        elif name == 'brk':
            s.pc += 1; s.push(s.pc >> 8); s.push(s.pc); s.push(s.p | B); s.p = (s.p | I) & ~D; s.pc = s.rd16(0xFFF6)
        else:
            raise RuntimeError('unhandled op %02x at %04x' % (op, pc0))
