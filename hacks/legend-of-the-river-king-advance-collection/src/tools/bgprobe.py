# Which BG tiles cover a screen rect, and where their 4bpp data comes from in the ROM (raw or LZ77 blocks).
import struct, pickle, sys
from drive import *
from lzscan import lz77

def bg_tiles(g, x0, y0, x1, y1):
    disp = g.r16(0x04000000)
    out = []
    for n in range(4):
        if not disp & (0x100 << n): continue
        cnt = g.r16(0x04000008 + 2 * n)
        hof = g.r16(0x04000010 + 4 * n) & 0x1ff; vof = g.r16(0x04000012 + 4 * n) & 0x1ff
        cb = ((cnt >> 2) & 3) * 0x4000; sb = ((cnt >> 8) & 31) * 0x800
        for ty in range(y0 // 8, (y1 + 7) // 8):
            row = []
            for tx in range(x0 // 8, (x1 + 7) // 8):
                mx = ((tx * 8 + hof) // 8) & 63; my = ((ty * 8 + vof) // 8) & 63
                blk = (mx // 32) + (my // 32) * (2 if (cnt >> 14) & 1 else 1) if (cnt >> 14) else 0
                e = g.r16(0x06000000 + sb + blk * 0x800 + ((my & 31) * 32 + (mx & 31)) * 2)
                row.append(e)
            out.append((n, cb, sb, ty, row))
    return out

_blocks = None
def blocks(rom):
    global _blocks
    if _blocks is None:
        refs = pickle.load(open('allrefs.pkl', 'rb'))
        _blocks = {}
        for off in sorted(refs):
            if off + 4 > len(rom) or rom[off] != 0x10: continue
            n = rom[off + 1] | rom[off + 2] << 8 | rom[off + 3] << 16
            if not (0x20 <= n <= 0x10000): continue
            try: d, ln = lz77(rom, off, limit=0x10000)
            except Exception: continue
            if len(d) == n: _blocks[off] = d
    return _blocks

def find_tile(rom, data):
    hits = []
    for off, d in blocks(rom).items():
        i = d.find(data)
        while i >= 0:
            if i % 32 == 0: hits.append(('lz', off, i // 32))
            i = d.find(data, i + 1)
    i = rom.find(data)
    while i >= 0 and len(hits) < 20:
        hits.append(('raw', i, None)); i = rom.find(data, i + 1)
    return hits
