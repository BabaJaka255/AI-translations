"""Kawa no Nushi Tsuri 5 helpers: ROM access, script table, decompression via the game's own routine."""
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import *

import os
ROM_PATH = os.environ.get('K5_ROM', os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'rom', 'k5.gba'))
SCRIPT_TABLE_PTR = 0x0803EBE0   # literal holding the script pointer table address
SCRIPT_COUNT = 0x11D
DECOMP = 0x08040D20

def u32(d, o): return struct.unpack_from('<I', d, o)[0]

class Rom:
    def __init__(self, path=ROM_PATH):
        self.d = open(path, 'rb').read()
        self.uc = None
    def ptr(self, a): return u32(self.d, a - 0x08000000)
    def script_table(self): return self.ptr(SCRIPT_TABLE_PTR)
    def script_ptrs(self):
        t = self.script_table()
        return [self.ptr(t + 4 * i) for i in range(SCRIPT_COUNT)]
    def _emu(self):
        if self.uc is None:
            uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
            rom = self.d + b'\0' * ((-len(self.d)) % 0x1000)
            uc.mem_map(0x08000000, len(rom)); uc.mem_write(0x08000000, rom)
            uc.mem_map(0x02000000, 0x40000); uc.mem_map(0x03000000, 0x8000)
            uc.mem_map(0x06000000, 0x18000)
            uc.mem_map(0x0F000000, 0x1000)
            self.uc = uc
        return self.uc
    def decompress(self, src, dst=0x02000000):
        uc = self._emu()
        size = self.ptr(src) >> 8
        uc.reg_write(UC_ARM_REG_R0, src); uc.reg_write(UC_ARM_REG_R1, dst)
        uc.reg_write(UC_ARM_REG_SP, 0x03007F00); uc.reg_write(UC_ARM_REG_LR, 0x0F000001)
        uc.emu_start(DECOMP | 1, 0x0F000000, count=50_000_000)
        return bytes(uc.mem_read(dst, size))
