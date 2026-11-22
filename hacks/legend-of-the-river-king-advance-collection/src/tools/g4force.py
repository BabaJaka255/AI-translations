# Draw a Kawa 4 shop window by calling its loader (0x80376D0) directly from a field state.
import sys
from drive import *
from unicorn.arm_const import *
def shop(R, idx, state='g4house', bro=None):
    g = loadrom(R, state); g.run_frames(5)
    g.press(['A'], hold=3, after=40)      # open the command panel so its VRAM is fresh
    B = 0x3000020
    g.wr(B + 0x295, bytes([0xe])); g.wr(B + 0x28e, bytes([idx // 3])); g.wr(B + 0x28f, bytes([idx % 3]))
    g.wr(B + 0x294, bytes([idx]))
    if bro is not None: g.wr(B + 0x2f1, bytes([bro]))
    uc = g.uc
    saved = {r: uc.reg_read(r) for r in (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)}
    uc.reg_write(UC_ARM_REG_SP, 0x03007d00)
    uc.reg_write(UC_ARM_REG_LR, 0x08000101)
    uc.emu_start(0x080376d1, 0x08000100, count=2000000)
    # the A-press handler (0x8030860) loads the map from 0x1F8320[idx] and fixes the title for idx 0 and 2
    import struct
    from lzscan import lz77
    rom = open(R, 'rb').read()
    m = struct.unpack_from('<I', rom, 0x1f8320 + 4 * idx)[0] - 0x08000000
    mp, _ = lz77(rom, m, limit=0x10000)
    g.wr(0x0600d800, mp)
    if idx in (0, 2):
        g.wr(0x0600d850, struct.pack('<4H', *rom[0x309a6:0x309ba:6]))
    g.h16(0x16, 0xffd8)    # BG1 (the window layer) scrolled into view as the shop does
    return g
if __name__ == '__main__':
    ims = []
    for R in ['../rom/k34.gba', 'k34_en.gba']:
        for i in range(8):
            g = shop(R, i); ims.append(g.render())
    sheet(ims, '../force.png', cols=4)
