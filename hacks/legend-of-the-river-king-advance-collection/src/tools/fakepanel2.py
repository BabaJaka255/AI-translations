# As fakepanel.py, but undo the field loader's own writes to row 1 cols 12-14 (the field's first command)
# before the panel is copied to the screen, so the variant panel shows as its own loader leaves it.
import sys, struct
sys.path.insert(0, '.')
from drive import *
from lzscan import lz77
from unicorn import UC_HOOK_MEM_READ
def show(R, maplit, setlit):
    rom = open(R, 'rb').read()
    L = lambda a: struct.unpack_from('<I', rom, a)[0]
    mapaddr, setaddr = L(maplit), L(setlit)
    mp, _ = lz77(rom, mapaddr - 0x08000000, limit=0x1000)
    g = loadrom(R, 'g3_fishing2'); g.run_frames(2)
    g.wr(0x08083310, struct.pack('<I', mapaddr)); g.wr(0x08084734, struct.pack('<I', setaddr))
    def hk(uc, acc, addr, size, val, ud):
        uc.mem_write(0x200D8E8 + 64 + 24, bytes(mp[64 + 24:64 + 30]))
    g.press(['B'], hold=4, after=40)
    h = g.uc.hook_add(UC_HOOK_MEM_READ, hk, begin=0x200D8E8 + 64, end=0x200D8E8 + 127)
    g.press(['A'], hold=4, after=60)
    g.uc.hook_del(h)
    return g
if __name__ == '__main__':
    ims = []
    for maplit, setlit in ((0x83698, 0x86160), (0x833c4, 0x8609c), (0x9e180, 0x9e178)):
        g = show('k34_en.gba', maplit, setlit); ims.append(g.render())
    sheet(ims, sys.argv[1], cols=3)
