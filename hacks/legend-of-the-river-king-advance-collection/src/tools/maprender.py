# Offline grey render of an LZ77 tile block + LZ77 map (patched ROM), for windows we cannot reach in play.
import sys, struct
import numpy as np
from PIL import Image
from lzscan import lz77
def render(rom, block, m, rows=14, cols=20, scale=2):
    blk, _ = lz77(rom, block, limit=0x10000); mp, _ = lz77(rom, m, limit=0x10000)
    hw = struct.unpack('<%dH' % (len(mp) // 2), mp)
    im = np.zeros((rows * 8, cols * 8), np.uint8)
    for r in range(rows):
        for c in range(cols):
            v = hw[r * 32 + c]; t = v & 0x3ff
            tile = blk[t * 32:t * 32 + 32]
            if len(tile) < 32: continue
            for y in range(8):
                for x in range(8):
                    b = tile[y * 4 + x // 2]; p = (b >> 4) if x & 1 else (b & 15)
                    im[r * 8 + (7 - y if v & 0x800 else y), c * 8 + (7 - x if v & 0x400 else x)] = 255 - p * 17
    return Image.fromarray(im).resize((cols * 8 * scale, rows * 8 * scale), Image.NEAREST)
if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    tb, tm = int(sys.argv[2], 16), int(sys.argv[3], 16)
    p = lambda a: struct.unpack_from('<I', rom, a)[0] - 0x08000000
    render(rom, p(tb), p(tm)).save(sys.argv[4])
