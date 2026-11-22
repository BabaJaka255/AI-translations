# Which 16-bit tile strings (ROM 0x1FE000-0x202400) are read while each tile block is loaded.
import struct
from unicorn import UC_HOOK_MEM_READ
import gba
from drive import *

class Tracer:
    def __init__(self, g):
        self.g = g; self.cur = {}; self.hits = {}
        o12 = gba.GBA.swi_12
        tr = self
        def s12(self_, r, pc):
            tr.cur[r[1]] = r[0]; o12(self_, r, pc)
        g.swi_12 = lambda r, pc: s12(g, r, pc)
        def rd(uc, access, addr, size, value, ud):
            key = (tr.cur.get(0x6000000), tr.cur.get(0x6001a00))
            tr.hits.setdefault(addr & ~1, set()).add(key)
        g.uc.hook_add(UC_HOOK_MEM_READ, rd, begin=0x081fe000, end=0x08202400)
