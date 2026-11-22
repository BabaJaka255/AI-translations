"""Minimal GBA emulator for translation testing: unicorn ARM core + HLE BIOS + numpy PPU.
Not cycle accurate. Good enough to boot, drive menus, read RAM/VRAM and take screenshots."""
import mmap, ctypes, struct, math
import numpy as np
from unicorn import *
from unicorn.arm_const import *

KEYS = {'A': 0, 'B': 1, 'SELECT': 2, 'START': 3, 'RIGHT': 4, 'LEFT': 5, 'UP': 6, 'DOWN': 7, 'R': 8, 'L': 9}
INSTR_PER_LINE = 300

def _buf(size):
    m = mmap.mmap(-1, size)
    addr = ctypes.addressof(ctypes.c_char.from_buffer(m))
    return m, addr

BIOS_CODE = {
    0x00: 0xEA00001E,  # b 0x80? (reset: unused)
    0x18: 0xEA000018,  # b 0x80
    0x80: 0xE92D500F,  # stmfd sp!,{r0-r3,r12,lr}
    0x84: 0xE3A00301,  # mov r0,#0x04000000
    0x88: 0xE28FE000,  # add lr,pc,#0  (lr=0x90)
    0x8C: 0xE510F004,  # ldr pc,[r0,#-4]
    0x90: 0xE8BD500F,  # ldmfd sp!,{r0-r3,r12,lr}
    0x94: 0xE25EF004,  # subs pc,lr,#4
}


class GBA:
    def __init__(self, rom, sram=None, trace_swi=False):
        self.rom = bytes(rom)
        uc = self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        try:
            uc.ctl_set_cpu_model(UC_CPU_ARM_946)
        except Exception:
            pass
        self.bufs = {}
        def region(name, base, size, mirrors=()):
            m, a = _buf(size)
            self.bufs[name] = m
            uc.mem_map_ptr(base, size, UC_PROT_ALL, a)
            for mb in mirrors:
                uc.mem_map_ptr(mb, size, UC_PROT_ALL, a)
            return m
        self.bios = region('bios', 0, 0x4000)
        self.ewram = region('ewram', 0x02000000, 0x40000)
        self.iwram = region('iwram', 0x03000000, 0x8000, [0x03FF8000])
        self.pal = region('pal', 0x05000000, 0x1000)
        self.vram = region('vram', 0x06000000, 0x20000)
        self.oam = region('oam', 0x07000000, 0x1000)
        romsize = (len(self.rom) + 0xFFFF) & ~0xFFFF
        romsize = max(romsize, 0x10000)
        self.rombuf = region('rom', 0x08000000, romsize, [0x0A000000, 0x0C000000])
        self.rombuf[:len(self.rom)] = self.rom
        self.sram = region('sram', 0x0E000000, 0x10000)
        if sram:
            self.sram[:len(sram)] = sram
        else:
            self.sram[:] = b'\xff' * 0x10000
        for a, v in BIOS_CODE.items():
            self.bios[a:a + 4] = struct.pack('<I', v)
        self.io = bytearray(0x400)
        uc.mmio_map(0x04000000, 0x1000, self._io_read, None, self._io_write, None)
        uc.hook_add(UC_HOOK_INTR, self._intr)
        uc.hook_add(UC_HOOK_MEM_INVALID, self._invalid)
        self.keys = 0
        self.line = 0
        self.frame = 0
        self.halted = None      # None, 'halt', or ('wait', mask, pc)
        self.dma_int = [None] * 4
        self.timers = [[0, 0, 0] for _ in range(4)]  # reload, counter, ctrl
        self.hbl_toggle = 0
        self.trace_swi = trace_swi
        self.swi_log = []
        self.stopped_err = None
        self.waiting_pc = None
        self.read_hooks = []
        # initial CPU state as after BIOS
        for mode, sp in ((0x12, 0x03007FA0), (0x13, 0x03007FE0), (0x1F, 0x03007F00)):
            uc.reg_write(UC_ARM_REG_CPSR, mode)
            uc.reg_write(UC_ARM_REG_SP, sp)
        self.pc = 0x08000000
        self.thumb = False
        self.h16(0x88, 0x200)  # SOUNDBIAS
        self.h16(0x130, 0x3FF)

    # ---------- IO ----------
    def h16(self, off, v=None):
        if v is None:
            return self.io[off] | self.io[off + 1] << 8
        self.io[off] = v & 0xFF
        self.io[off + 1] = (v >> 8) & 0xFF

    def _io_read(self, uc, off, size, ud):
        if off >= 0x400:
            return 0
        v = 0
        for i in range(0, size, 2) if size >= 2 else [0]:
            o = (off + i) & ~1
            hv = self._read_h(o)
            if size == 1:
                return (hv >> (8 * (off & 1))) & 0xFF
            v |= hv << (8 * i)
        return v

    def _read_h(self, o):
        if o == 0x04:
            ds = self.h16(4) & 0xFFF8
            ln = self.line
            if 160 <= ln < 227:
                ds |= 1
            self.hbl_toggle ^= 1
            if self.hbl_toggle:
                ds |= 2
            if ln == (ds >> 8):
                ds |= 4
            return ds
        if o == 0x06:
            return self.line
        if o == 0x130:
            return 0x3FF & ~self.keys
        if 0x100 <= o < 0x110 and (o & 3) == 0:
            return self.timers[(o - 0x100) >> 2][1] & 0xFFFF
        return self.h16(o)

    def _io_write(self, uc, off, size, value, ud):
        if off >= 0x400:
            return
        if size == 4:
            self._write_h(off, value & 0xFFFF, 0xFFFF)
            self._write_h(off + 2, (value >> 16) & 0xFFFF, 0xFFFF)
        elif size == 2:
            self._write_h(off, value & 0xFFFF, 0xFFFF)
        else:
            o = off & ~1
            sh = 8 * (off & 1)
            self._write_h(o, (value & 0xFF) << sh, 0xFF << sh)

    def _write_h(self, o, v, mask):
        if o == 0x202:  # IF: write 1 to clear
            self.h16(0x202, self.h16(0x202) & ~(v & mask))
            return
        if o == 0x300:  # POSTFLG/HALTCNT
            if mask & 0xFF00:
                self.halted = 'halt'
                self.uc.emu_stop()
            self.io[0x300] = v & 0xFF if mask & 0xFF else self.io[0x300]
            return
        old = self.h16(o)
        new = (old & ~mask) | (v & mask)
        if o == 0x04:
            new = (new & 0xFFF8) | (old & 7)
        if 0x100 <= o < 0x110:
            n = (o - 0x100) >> 2
            if o & 2:
                if (new & 0x80) and not (old & 0x80):
                    self.timers[n][1] = self.timers[n][0]
                self.timers[n][2] = new
            else:
                self.timers[n][0] = new
                return
        self.h16(o, new)
        if 0xB0 <= o < 0xE0 and (o - 0xB0) % 12 == 10:
            n = (o - 0xB0) // 12
            if (new & 0x8000) and not (old & 0x8000):
                b = 0xB0 + 12 * n
                src = struct.unpack_from('<I', self.io, b)[0]
                dst = struct.unpack_from('<I', self.io, b + 4)[0]
                cnt = self.h16(b + 8)
                self.dma_int[n] = [src, dst, cnt]
                if (new >> 12) & 3 == 0:
                    self._run_dma(n)

    def _run_dma(self, n):
        b = 0xB0 + 12 * n
        ctl = self.h16(b + 10)
        timing = (ctl >> 12) & 3
        if timing == 3:
            return
        src, dst, cnt = self.dma_int[n]
        if cnt == 0:
            cnt = 0x10000 if n == 3 else 0x4000
        word = ctl & 0x400
        unit = 4 if word else 2
        sc = (ctl >> 7) & 3
        dc = (ctl >> 5) & 3
        src &= 0x0FFFFFFE if not word else 0x0FFFFFFC
        dst &= 0x0FFFFFFE if not word else 0x0FFFFFFC
        uc = self.uc
        sstep = {0: unit, 1: -unit, 2: 0, 3: unit}[sc]
        dstep = {0: unit, 1: -unit, 2: 0, 3: unit}[dc]
        try:
            if sstep == unit and dstep == unit and not (0x04000000 <= dst < 0x05000000) and not (0x04000000 <= src < 0x05000000):
                data = uc.mem_read(src, cnt * unit)
                uc.mem_write(dst, bytes(data))
            else:
                s, d = src, dst
                for i in range(cnt):
                    if 0x04000000 <= s < 0x05000000:
                        val = self._io_read(uc, s - 0x04000000, unit, None)
                    else:
                        val = int.from_bytes(uc.mem_read(s, unit), 'little')
                    if 0x04000000 <= d < 0x05000000:
                        self._io_write(uc, d - 0x04000000, unit, val, None)
                    else:
                        uc.mem_write(d, val.to_bytes(unit, 'little'))
                    s += sstep
                    d += dstep
        except UcError:
            pass
        self.dma_int[n][0] = src + sstep * cnt
        if dc != 3:
            self.dma_int[n][1] = dst + dstep * cnt
        if ctl & 0x4000:
            self.h16(0x202, self.h16(0x202) | (1 << (8 + n)))
        if not (ctl & 0x200) or timing == 0:
            self.h16(b + 10, ctl & 0x7FFF)
        else:
            self.dma_int[n][2] = self.h16(b + 8)

    # ---------- BIOS HLE ----------
    def _invalid(self, uc, access, addr, size, value, ud):
        # map unmapped memory on the fly (open bus)
        try:
            uc.mem_map(addr & ~0xFFF, 0x1000)
        except UcError:
            pass
        return True

    def _intr(self, uc, intno, ud):
        if intno != 2:
            self.stopped_err = 'intr %d at %x' % (intno, uc.reg_read(UC_ARM_REG_PC))
            uc.emu_stop()
            return
        pc = uc.reg_read(UC_ARM_REG_PC)
        cpsr = uc.reg_read(UC_ARM_REG_CPSR)
        if cpsr & 0x20:
            num = uc.mem_read(pc - 2, 1)[0]
            swi_pc = pc - 2
        else:
            num = (struct.unpack('<I', uc.mem_read(pc - 4, 4))[0] >> 16) & 0xFF
            swi_pc = pc - 4
        if self.trace_swi:
            self.swi_log.append((self.frame, num, swi_pc))
        r = [uc.reg_read(UC_ARM_REG_R0 + i) for i in range(4)]
        f = getattr(self, 'swi_%02x' % num, None)
        if f is None:
            print('unhandled SWI %02x at %08x' % (num, swi_pc))
            return
        f(r, swi_pc)

    def _set(self, *vals):
        for i, v in enumerate(vals):
            if v is not None:
                self.uc.reg_write(UC_ARM_REG_R0 + i, v & 0xFFFFFFFF)

    def rd(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def wr(self, a, data):
        self.uc.mem_write(a, bytes(data))

    def r32(self, a):
        return struct.unpack('<I', self.rd(a, 4))[0]

    def r16(self, a):
        return struct.unpack('<H', self.rd(a, 2))[0]

    def swi_00(self, r, pc):
        print('SoftReset')

    def swi_01(self, r, pc):
        f = r[0]
        if f & 1: self.wr(0x02000000, bytes(0x40000))
        if f & 2: self.wr(0x03000000, bytes(0x7E00))
        if f & 4: self.wr(0x05000000, bytes(0x400))
        if f & 8: self.wr(0x06000000, bytes(0x18000))
        if f & 16: self.wr(0x07000000, bytes(0x400))

    def swi_02(self, r, pc):
        self.halted = 'halt'
        self.uc.emu_stop()

    def _intrwait(self, discard, mask, pc):
        flags = self.r16(0x03007FF8)
        if self.waiting_pc == pc:
            if flags & mask:
                self.wr(0x03007FF8, struct.pack('<H', flags & ~mask))
                self.waiting_pc = None
                return
        else:
            if discard:
                self.wr(0x03007FF8, struct.pack('<H', flags & ~mask))
            elif flags & mask:
                self.wr(0x03007FF8, struct.pack('<H', flags & ~mask))
                return
        self.waiting_pc = pc
        self.halted = ('wait', mask, pc)
        self.h16(0x208, 1)
        self.uc.emu_stop()

    def swi_04(self, r, pc):
        self._intrwait(r[0], r[1], pc)

    def swi_05(self, r, pc):
        self._intrwait(1, 1, pc)

    def _div(self, n, d):
        n = n - (1 << 32) if n & 0x80000000 else n
        d = d - (1 << 32) if d & 0x80000000 else d
        if d == 0:
            return (1 if n >= 0 else -1), n, 1
        q = abs(n) // abs(d)
        if (n < 0) != (d < 0):
            q = -q
        rem = n - q * d
        return q, rem, abs(q)

    def swi_06(self, r, pc):
        q, m, a = self._div(r[0], r[1])
        self._set(q, m, a)

    def swi_07(self, r, pc):
        q, m, a = self._div(r[1], r[0])
        self._set(q, m, a)

    def swi_08(self, r, pc):
        self._set(int(math.isqrt(r[0])))

    def swi_09(self, r, pc):
        x = r[0] - (1 << 32) if r[0] & 0x80000000 else r[0]
        a = math.atan(x / 16384.0)
        self._set(int(a / (math.pi / 2) * 0x4000))

    def swi_0a(self, r, pc):
        x = r[0] - (1 << 32) if r[0] & 0x80000000 else r[0]
        y = r[1] - (1 << 32) if r[1] & 0x80000000 else r[1]
        a = math.atan2(y, x)
        if a < 0:
            a += 2 * math.pi
        self._set(int(a / (2 * math.pi) * 0x10000) & 0xFFFF)

    def swi_0b(self, r, pc):  # CpuSet
        src, dst, cnt = r[0], r[1], r[2]
        n = cnt & 0x1FFFFF
        unit = 4 if cnt & (1 << 26) else 2
        if cnt & (1 << 24):
            v = self.rd(src, unit)
            self.wr(dst, v * n)
        else:
            self.wr(dst, self.rd(src, n * unit))

    def swi_0c(self, r, pc):  # CpuFastSet
        src, dst, cnt = r[0], r[1], r[2]
        n = (cnt & 0x1FFFFF)
        n = (n + 7) & ~7
        if cnt & (1 << 24):
            self.wr(dst, self.rd(src, 4) * n)
        else:
            self.wr(dst, self.rd(src, n * 4))

    def swi_0d(self, r, pc):
        self._set(0xBAAE187F)

    def swi_0e(self, r, pc):  # BgAffineSet
        src, dst, n = r[0], r[1], r[2]
        for i in range(n):
            ox, oy, cx, cy, sx, sy, th = struct.unpack('<iihhhhH', self.rd(src + i * 20, 18))
            a = th / 65536 * 2 * math.pi
            c, s = math.cos(a), math.sin(a)
            pa = int(c * 256 * sx / 256); pb = int(-s * 256 * sx / 256)
            pc_ = int(s * 256 * sy / 256); pd = int(c * 256 * sy / 256)
            x0 = ox - (pa * cx + pb * cy)
            y0 = oy - (pc_ * cx + pd * cy)
            self.wr(dst + i * 16, struct.pack('<hhhhii', pa, pb, pc_, pd, x0, y0))

    def swi_0f(self, r, pc):  # ObjAffineSet
        src, dst, n, off = r
        for i in range(n):
            sx, sy, th = struct.unpack('<hhH', self.rd(src + i * 8, 6))
            a = (th >> 8) / 256 * 2 * math.pi
            c, s = math.cos(a), math.sin(a)
            vals = [int(c * sx), int(-s * sx), int(s * sy), int(c * sy)]
            for k, v in enumerate(vals):
                self.wr(dst + i * off * 4 + k * off, struct.pack('<h', v))

    def swi_10(self, r, pc):  # BitUnPack
        src, dst, info = r[0], r[1], r[2]
        ln, sw, dw, off = struct.unpack('<HBBI', self.rd(info, 8))
        data = self.rd(src, ln)
        zero = off >> 31
        off &= 0x7FFFFFFF
        out = 0; bits = 0; res = bytearray()
        for byte in data:
            for k in range(0, 8, sw):
                v = (byte >> k) & ((1 << sw) - 1)
                if v or zero:
                    v += off
                out |= (v & ((1 << dw) - 1)) << bits
                bits += dw
                if bits >= 32:
                    res += struct.pack('<I', out & 0xFFFFFFFF); out = 0; bits = 0
        self.wr(dst, res)

    def lz77(self, src):
        hdr = self.r32(src)
        size = hdr >> 8
        data = self.rd(src + 4, min(size * 2 + 0x100, 0x0A000000 - src if src >= 0x08000000 else size * 2 + 0x100))
        out = bytearray(); i = 0
        while len(out) < size:
            flags = data[i]; i += 1
            for k in range(8):
                if len(out) >= size:
                    break
                if flags & (0x80 >> k):
                    b1, b2 = data[i], data[i + 1]; i += 2
                    ln = (b1 >> 4) + 3
                    disp = ((b1 & 0xF) << 8 | b2) + 1
                    for _ in range(ln):
                        out.append(out[-disp])
                else:
                    out.append(data[i]); i += 1
        return bytes(out[:size])

    def swi_11(self, r, pc):
        self.wr(r[1], self.lz77(r[0]))

    def swi_12(self, r, pc):
        d = self.lz77(r[0])
        if len(d) & 1:
            d += b'\0'
        self.wr(r[1], d)

    def swi_13(self, r, pc):  # HuffUnComp
        src, dst = r[0], r[1]
        hdr = self.r32(src)
        bits = hdr & 0xF
        size = hdr >> 8
        tsize = (self.rd(src + 4, 1)[0] + 1) * 2
        tree = src + 5
        data = src + 4 + tsize
        out = bytearray(); acc = 0; nb = 0
        node = tree; pos = 0
        word = 0; wbits = 0
        while len(out) < size:
            w = self.r32(data + pos); pos += 4
            for k in range(31, -1, -1):
                bit = (w >> k) & 1
                nv = self.rd(node, 1)[0]
                nxt = (node & ~1) + (nv & 0x3F) * 2 + 2
                child = nxt + bit
                isleaf = nv & (0x80 if bit == 0 else 0x40)
                if isleaf:
                    val = self.rd(child, 1)[0]
                    acc |= val << nb; nb += bits
                    node = tree
                    if nb == 32:
                        out += struct.pack('<I', acc); acc = 0; nb = 0
                        if len(out) >= size:
                            break
                else:
                    node = child
        self.wr(dst, out[:size])

    def rl(self, src):
        hdr = self.r32(src)
        size = hdr >> 8
        p = src + 4; out = bytearray()
        while len(out) < size:
            f = self.rd(p, 1)[0]; p += 1
            if f & 0x80:
                n = (f & 0x7F) + 3
                out += self.rd(p, 1) * n; p += 1
            else:
                n = (f & 0x7F) + 1
                out += self.rd(p, n); p += n
        return bytes(out[:size])

    def swi_14(self, r, pc):
        self.wr(r[1], self.rl(r[0]))

    def swi_15(self, r, pc):
        self.wr(r[1], self.rl(r[0]))

    def swi_16(self, r, pc):
        hdr = self.r32(r[0]); size = hdr >> 8
        d = bytearray(self.rd(r[0] + 4, size))
        for i in range(1, size):
            d[i] = (d[i] + d[i - 1]) & 0xFF
        self.wr(r[1], d)
    swi_17 = swi_16

    def swi_18(self, r, pc):
        hdr = self.r32(r[0]); size = hdr >> 8
        d = list(struct.unpack('<%dH' % (size // 2), self.rd(r[0] + 4, size)))
        for i in range(1, len(d)):
            d[i] = (d[i] + d[i - 1]) & 0xFFFF
        self.wr(r[1], struct.pack('<%dH' % len(d), *d))

    def swi_19(self, r, pc):
        pass

    def swi_1f(self, r, pc):  # MidiKey2Freq
        wa, mk, fp = r[0], r[1], r[2]
        freq = self.r32(wa + 4)
        v = freq / (2 ** ((180 - mk - fp / 256) / 12))
        self._set(int(v))

    for _n in (0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2a):
        locals()['swi_%02x' % _n] = lambda self, r, pc: None

    # ---------- execution ----------
    def _irq_pending(self):
        return (self.h16(0x208) & 1) and (self.h16(0x200) & self.h16(0x202) & 0x3FFF)

    def _enter_irq(self):
        uc = self.uc
        cpsr = uc.reg_read(UC_ARM_REG_CPSR)
        if cpsr & 0x80:
            return False
        pc = self.pc
        if isinstance(self.halted, tuple):
            pc = self.halted[2]   # re-execute IntrWait after handler
        self.halted = None
        uc.reg_write(UC_ARM_REG_CPSR, 0x92)
        uc.reg_write(UC_ARM_REG_SPSR, cpsr)
        uc.reg_write(UC_ARM_REG_LR, pc + 4)
        self.pc = 0x18
        self.thumb = False
        return True

    def _run(self, count):
        uc = self.uc
        start = self.pc | (1 if self.thumb else 0)
        try:
            uc.emu_start(start, 0xFFFFFFFF, count=count)
        except UcError as e:
            self.stopped_err = '%s at pc=%08x' % (e, uc.reg_read(UC_ARM_REG_PC))
            raise
        self.pc = uc.reg_read(UC_ARM_REG_PC)
        self.thumb = bool(uc.reg_read(UC_ARM_REG_CPSR) & 0x20)

    def _timers_tick(self, cycles):
        prescale = (1, 64, 256, 1024)
        for n in range(4):
            reload, cnt, ctl = self.timers[n]
            if not (ctl & 0x80) or (ctl & 4):
                continue
            ticks = cycles // prescale[ctl & 3]
            cnt += ticks
            ov = 0
            while cnt > 0xFFFF:
                cnt = cnt - 0x10000 + reload
                ov += 1
                if 0x10000 - reload <= 0:
                    break
            if ov and (ctl & 0x40):
                self.h16(0x202, self.h16(0x202) | (8 << n))
            self.timers[n][1] = cnt & 0xFFFF

    def step_line(self):
        ln = self.line
        ds = self.h16(4)
        if ln == 160:
            if ds & 8:
                self.h16(0x202, self.h16(0x202) | 1)
            for n in range(4):
                c = self.h16(0xB0 + 12 * n + 10)
                if (c & 0x8000) and ((c >> 12) & 3) == 1:
                    self._run_dma(n)
        if ln == (ds >> 8) and (ds & 0x20):
            self.h16(0x202, self.h16(0x202) | 4)
        budget = INSTR_PER_LINE
        if self._irq_pending():
            self._enter_irq()
        if self.halted is None:
            self._run(budget)
        if ln < 160:
            if ds & 0x10:
                self.h16(0x202, self.h16(0x202) | 2)
            for n in range(4):
                c = self.h16(0xB0 + 12 * n + 10)
                if (c & 0x8000) and ((c >> 12) & 3) == 2:
                    self._run_dma(n)
        self._timers_tick(1232)
        self.line = (ln + 1) % 228
        if self.line == 0:
            self.frame += 1

    def run_frames(self, n=1, keys=None):
        if keys is not None:
            self.set_keys(keys)
        for _ in range(n * 228):
            self.step_line()

    def set_keys(self, keys):
        k = 0
        if isinstance(keys, str):
            keys = [x for x in keys.split('+') if x]
        for x in keys:
            k |= 1 << KEYS[x.upper()]
        self.keys = k

    def press(self, keys, hold=4, after=20):
        self.run_frames(hold, keys)
        self.run_frames(after, [])

    # ---------- state ----------
    def save_state(self):
        regs = {}
        uc = self.uc
        cpsr = uc.reg_read(UC_ARM_REG_CPSR)
        banked = {}
        for mode in (0x12, 0x13, 0x1F, 0x17, 0x1B):
            uc.reg_write(UC_ARM_REG_CPSR, (cpsr & ~0x1F) | mode)
            banked[mode] = (uc.reg_read(UC_ARM_REG_SP), uc.reg_read(UC_ARM_REG_LR), uc.reg_read(UC_ARM_REG_SPSR))
        uc.reg_write(UC_ARM_REG_CPSR, cpsr)
        gp = [uc.reg_read(UC_ARM_REG_R0 + i) for i in range(13)]
        return dict(cpsr=cpsr, banked=banked, gp=gp, lr=uc.reg_read(UC_ARM_REG_LR), sp=uc.reg_read(UC_ARM_REG_SP),
                    pc=self.pc, thumb=self.thumb, io=bytes(self.io), line=self.line, frame=self.frame,
                    halted=self.halted, waiting_pc=self.waiting_pc, timers=[list(t) for t in self.timers],
                    dma=[list(x) if x else None for x in self.dma_int],
                    mem={k: bytes(v[:]) for k, v in self.bufs.items() if k not in ('rom', 'bios')})

    def load_state(self, s):
        uc = self.uc
        for k, v in s['mem'].items():
            self.bufs[k][:len(v)] = v
        cpsr = s['cpsr']
        for mode, (sp, lr, spsr) in s['banked'].items():
            uc.reg_write(UC_ARM_REG_CPSR, (cpsr & ~0x1F) | mode)
            uc.reg_write(UC_ARM_REG_SP, sp); uc.reg_write(UC_ARM_REG_LR, lr); uc.reg_write(UC_ARM_REG_SPSR, spsr)
        uc.reg_write(UC_ARM_REG_CPSR, cpsr)
        for i, v in enumerate(s['gp']):
            uc.reg_write(UC_ARM_REG_R0 + i, v)
        uc.reg_write(UC_ARM_REG_LR, s['lr']); uc.reg_write(UC_ARM_REG_SP, s['sp'])
        self.pc = s['pc']; self.thumb = s['thumb']; self.io = bytearray(s['io']); self.line = s['line']
        self.frame = s['frame']; self.halted = s['halted']; self.waiting_pc = s['waiting_pc']
        self.timers = [list(t) for t in s['timers']]; self.dma_int = [list(x) if x else None for x in s['dma']]

    # ---------- PPU ----------
    def palette(self):
        p = np.frombuffer(self.pal[:0x400], dtype='<u2').astype(np.uint32)
        r = (p & 31) << 3; g = ((p >> 5) & 31) << 3; b = ((p >> 10) & 31) << 3
        return np.stack([r, g, b], -1).astype(np.uint8)

    def render(self):
        from PIL import Image
        io = self.io
        dispcnt = self.h16(0)
        mode = dispcnt & 7
        pal = self.palette()
        vram = np.frombuffer(self.vram[:0x18000], dtype=np.uint8)
        W, H = 240, 160
        img = np.zeros((H, W, 3), np.uint8)
        img[:] = pal[0]
        if dispcnt & 0x80:
            img[:] = 255
            return Image.fromarray(img)
        layers = []  # (prio, order, rgb, mask)
        def text_bg(n):
            cnt = self.h16(8 + 2 * n)
            hofs = self.h16(0x10 + 4 * n) & 0x1FF
            vofs = self.h16(0x12 + 4 * n) & 0x1FF
            cb = ((cnt >> 2) & 3) * 0x4000
            sb = ((cnt >> 8) & 31) * 0x800
            c256 = cnt & 0x80
            size = cnt >> 14
            mw = 64 if size & 1 else 32
            mh = 64 if size & 2 else 32
            ys = (np.arange(H) + vofs) % (mh * 8)
            xs = (np.arange(W) + hofs) % (mw * 8)
            ty = ys // 8; tx = xs // 8
            TY, TX = np.meshgrid(ty, tx, indexing='ij')
            blk = (TX // 32) + (TY // 32) * (2 if mw == 64 else 1)
            idx = sb + blk * 0x800 + ((TY % 32) * 32 + (TX % 32)) * 2
            idx = np.clip(idx, 0, 0x17FFE)
            ent = vram[idx].astype(np.int32) | (vram[idx + 1].astype(np.int32) << 8)
            tile = ent & 0x3FF; hf = (ent >> 10) & 1; vf = (ent >> 11) & 1; pb = ent >> 12
            PY, PX = np.meshgrid(ys % 8, xs % 8, indexing='ij')
            PX = np.where(hf, 7 - PX, PX); PY = np.where(vf, 7 - PY, PY)
            if c256:
                a = cb + tile * 64 + PY * 8 + PX
                a = np.clip(a, 0, 0x17FFF)
                ci = vram[a].astype(np.int32)
                col = ci
            else:
                a = cb + tile * 32 + PY * 4 + PX // 2
                a = np.clip(a, 0, 0x17FFF)
                v = vram[a].astype(np.int32)
                ci = np.where(PX & 1, v >> 4, v & 15)
                col = pb * 16 + ci
            return pal[col], ci != 0, cnt & 3
        def affine_bg(n):
            cnt = self.h16(8 + 2 * n)
            cb = ((cnt >> 2) & 3) * 0x4000
            sb = ((cnt >> 8) & 31) * 0x800
            size = 128 << (cnt >> 14)
            base = 0x20 + (n - 2) * 0x10
            pa, pb_, pc_, pd = struct.unpack_from('<hhhh', io, base)
            x0, y0 = struct.unpack_from('<ii', io, base + 8)
            x0 = (x0 << 4) >> 4; y0 = (y0 << 4) >> 4
            Y, X = np.meshgrid(np.arange(H), np.arange(W), indexing='ij')
            tx = (x0 + pa * X + pb_ * Y) >> 8
            ty = (y0 + pc_ * X + pd * Y) >> 8
            wrap = cnt & 0x2000
            if wrap:
                tx %= size; ty %= size; inside = np.ones_like(tx, bool)
            else:
                inside = (tx >= 0) & (ty >= 0) & (tx < size) & (ty < size)
                tx = np.clip(tx, 0, size - 1); ty = np.clip(ty, 0, size - 1)
            ti = vram[np.clip(sb + (ty // 8) * (size // 8) + tx // 8, 0, 0x17FFF)].astype(np.int32)
            ci = vram[np.clip(cb + ti * 64 + (ty % 8) * 8 + tx % 8, 0, 0x17FFF)].astype(np.int32)
            return pal[ci], (ci != 0) & inside, cnt & 3
        bgs = []
        if mode == 0:
            bgs = [(n, text_bg) for n in range(4)]
        elif mode == 1:
            bgs = [(0, text_bg), (1, text_bg), (2, affine_bg)]
        elif mode == 2:
            bgs = [(2, affine_bg), (3, affine_bg)]
        for n, fn in bgs:
            if dispcnt & (0x100 << n):
                rgb, m, pr = fn(n)
                layers.append((pr, 0, n, rgb, m))
        if mode in (3, 4, 5) and dispcnt & 0x400:
            if mode == 3:
                p = np.frombuffer(self.vram[:240 * 160 * 2], dtype='<u2').reshape(160, 240).astype(np.uint32)
                rgb = np.stack([(p & 31) << 3, ((p >> 5) & 31) << 3, ((p >> 10) & 31) << 3], -1).astype(np.uint8)
                m = np.ones((H, W), bool)
            elif mode == 4:
                off = 0xA000 if dispcnt & 0x10 else 0
                ci = vram[off:off + 240 * 160].reshape(160, 240)
                rgb = pal[ci]; m = ci != 0
            else:
                off = 0xA000 if dispcnt & 0x10 else 0
                p = np.frombuffer(self.vram[off:off + 160 * 128 * 2], dtype='<u2').reshape(128, 160).astype(np.uint32)
                rgb = np.zeros((H, W, 3), np.uint8); m = np.zeros((H, W), bool)
                rgb[:128, :160] = np.stack([(p & 31) << 3, ((p >> 5) & 31) << 3, ((p >> 10) & 31) << 3], -1)
                m[:128, :160] = True
            pr = self.h16(0xC) & 3
            layers.append((pr, 0, 2, rgb, m))
        # sprites
        if dispcnt & 0x1000:
            oam = bytes(self.oam[:0x400])
            obj1d = dispcnt & 0x40
            sprite_layers = {p: (np.zeros((H, W, 3), np.uint8), np.zeros((H, W), bool)) for p in range(4)}
            shapes = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
                      (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
                      (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}
            objbase = 0x10000
            for i in range(127, -1, -1):
                a0, a1, a2 = struct.unpack_from('<HHH', oam, i * 8)
                affine = a0 & 0x100
                if not affine and (a0 & 0x200):
                    continue
                if (a0 >> 10) & 3 == 2:  # obj window
                    continue
                shape = a0 >> 14
                if shape == 3:
                    continue
                w, h = shapes[(shape, a1 >> 14)]
                y = a0 & 0xFF; x = a1 & 0x1FF
                if x >= 240: x -= 512
                if y >= 160: y -= 256
                c256 = a0 & 0x2000
                tile = a2 & 0x3FF; pr = (a2 >> 10) & 3; pb = a2 >> 12
                if mode >= 3 and tile < 512:
                    continue
                dbl = affine and (a0 & 0x200)
                bw, bh = (w * 2, h * 2) if dbl else (w, h)
                Y, X = np.meshgrid(np.arange(bh), np.arange(bw), indexing='ij')
                if affine:
                    g = (a1 >> 9) & 31
                    pa, pb2, pc2, pd = [struct.unpack_from('<h', oam, g * 32 + 6 + 8 * k)[0] for k in range(4)]
                    cx, cy = bw / 2, bh / 2
                    tx = ((pa * (X - cx) + pb2 * (Y - cy)) / 256 + w / 2).astype(int)
                    ty = ((pc2 * (X - cx) + pd * (Y - cy)) / 256 + h / 2).astype(int)
                    ok = (tx >= 0) & (ty >= 0) & (tx < w) & (ty < h)
                    tx = np.clip(tx, 0, w - 1); ty = np.clip(ty, 0, h - 1)
                else:
                    tx = np.where(a1 & 0x1000, w - 1 - X, X)
                    ty = np.where(a1 & 0x2000, h - 1 - Y, Y)
                    ok = np.ones_like(tx, bool)
                tcx = tx // 8; tcy = ty // 8
                if c256:
                    row = (w // 8) * 2 if obj1d else 32
                    tn = tile + tcy * row + tcx * 2
                    addr = objbase + (tn & 0x3FF) * 32 + (ty % 8) * 8 + tx % 8
                    ci = vram[np.clip(addr, 0, 0x17FFF)].astype(np.int32)
                    col = 256 + ci
                else:
                    row = (w // 8) if obj1d else 32
                    tn = tile + tcy * row + tcx
                    addr = objbase + (tn & 0x3FF) * 32 + (ty % 8) * 4 + (tx % 8) // 2
                    v = vram[np.clip(addr, 0, 0x17FFF)].astype(np.int32)
                    ci = np.where((tx % 8) & 1, v >> 4, v & 15)
                    col = 256 + pb * 16 + ci
                m = ok & (ci != 0)
                sy, sx = Y + y, X + x
                vis = m & (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
                rgb, mm = sprite_layers[pr]
                rgb[sy[vis], sx[vis]] = pal[col[vis]]
                mm[sy[vis], sx[vis]] = True
            for p, (rgb, mm) in sprite_layers.items():
                layers.append((p, 1, -1, rgb, mm))
        layers.sort(key=lambda t: (-t[0], t[1], -t[2]))
        for pr, kind, n, rgb, m in layers:
            img[m] = rgb[m]
        bld = self.h16(0x50)
        eff = (bld >> 6) & 3
        if eff in (2, 3):
            y = min(16, self.io[0x54] & 31)
            f = img.astype(np.int32)
            if eff == 2:
                f = f + (255 - f) * y // 16
            else:
                f = f - f * y // 16
            img = f.clip(0, 255).astype(np.uint8)
        return Image.fromarray(img)

    def shot(self, path, scale=2):
        im = self.render()
        if scale != 1:
            from PIL import Image
            im = im.resize((240 * scale, 160 * scale), Image.NEAREST)
        im.save(path)
        return im
