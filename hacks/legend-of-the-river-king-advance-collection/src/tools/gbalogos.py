# English title logos (the tester's art): the 3&4 start screen and the game select screen show the logos as sprites
# through the title metasprite engine; the game 3 / game 4 title pictures have the logo painted into the
# 240x160 mode-4 bitmap.
#   start screen: tiles 0xC1A70 -> 0x6014000 (logo rows 0-7, copyright rows 8-9 cols 0-23, rows 10-11 free),
#                 palette 0xC2BCC -> OBJ palettes from 0 (pal 1 = copyright; 2-9 are reloaded later by 0xC4534),
#                 frame list = first entry of table 0x202130
#   select:       game 3 logo tiles 0xC2C08 -> 0x6014000, palette 0xC3648 (pal 0), frame table 0x2021B0
#                 game 4 logo tiles 0xC3670 -> 0x6016000, palette 0xC4174 (pal 1), frame table 0x20222C
#                 one palette each: the unselected logo is dimmed by fading that palette
#   title pictures: game 3 bitmap 0x2240F4 + palette 0x227768, game 4 bitmap 0x2278D0 + palette 0x22D458
import os, pickle, struct
import numpy as np
from PIL import Image
from lzscan import lz77
from namekbd import put_lz
import logopack

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, 'logos')
_fb = np.ones((12, 32), bool); _fb[8:10, 0:24] = False
SPRITES = [
    # name, art, width, free char grid, max pieces, palettes, logo centre rel. to metasprite, tiles, pal, table
    ('start', 'collection.png', 210, _fb, 20, [0, 10, 11, 12, 13, 14, 15], (0, -12), 0xc1a70, 0xc2bcc, 0x202130),
    ('select3', 'kawa3.png', 190, np.ones((8, 32), bool), 15, [0], (0, -10), 0xc2c08, 0xc3648, 0x2021b0),
    ('select4', 'kawa4.png', 180, np.ones((8, 32), bool), 15, [0], (0, -14), 0xc3670, 0xc4174, 0x20222c),
]
PICTURES = [('t3', 0x2240f4, 0x227768), ('t4', 0x2278d0, 0x22d458)]
CACHE = os.path.join(HERE, 'logo_cache.pkl')

def sprites():
    key = [(s[0], s[1], s[2], s[4], tuple(s[5]), s[6], os.path.getmtime(os.path.join(ART, s[1]))) for s in SPRITES]
    if os.path.exists(CACHE):
        c = pickle.load(open(CACHE, 'rb'))
        if c['key'] == key: return c['res']
    res = {s[0]: logopack.build(os.path.join(ART, s[1]), s[2], s[3], s[4], s[5], s[6]) for s in SPRITES}
    pickle.dump(dict(key=key, res=res), open(CACHE, 'wb'))
    return res

# the engine gives every sprite its own affine matrix (counter 0x3002DB4) but stored only 3 bits of the index
# in the OAM entry, so more than 8 sprites wrapped onto each other's matrices; keep all 5 bits instead
MATRIX_INDEX = [(0xbba3e, b'\x07\x22', b'\x1f\x22'),    # movs r2,#7    -> #0x1f
                (0xbba48, b'\xf1\x23', b'\xc1\x23')]    # movs r3,#0xf1 -> #0xc1

def apply(rom, allrefs):
    for off, old, new in MATRIX_INDEX:
        assert bytes(rom.d[off:off + 2]) == old
        rom.w(off, new)
    res = sprites()
    for name, art, w, free, maxp, pals, cen, tiles, pal, table in SPRITES:
        r = res[name]
        blk, ln = lz77(rom.d, tiles, limit=0x10000)
        blk = bytearray(blk) + bytes(max(0, free.shape[0] * 32 * 32 - len(blk)))
        # clear the old logo (every free tile), then write the new pieces
        for t in range(free.size):
            if free.flat[t]: blk[t * 32:t * 32 + 32] = bytes(32)
        for t, data in r['charmap'].items(): blk[t * 32:t * 32 + 32] = data
        put_lz(rom, allrefs, tiles, ln, bytes(blk))
        pblk, pln = lz77(rom.d, pal, limit=0x1000)
        pblk = bytearray(pblk) + bytes(max(0, (max(pals) + 1) * 32 - len(pblk)))
        for p, cols in r['pals'].items():
            pblk[p * 32:p * 32 + 32] = struct.pack('<16H', *cols)
        put_lz(rom, allrefs, pal, pln, bytes(pblk))
        a = rom.put(r['frame'], align=4)
        rom.w(table, struct.pack('<I', 0x08000000 + a))
    for nm, bm, pl in PICTURES:
        im = Image.open(os.path.join(ART, nm + '_title.png'))
        assert im.mode == 'P' and im.size == (240, 160)
        idx = bytes(im.getdata())
        p = im.getpalette()[:768] + [0] * max(0, 768 - len(im.getpalette()))
        cols = [((p[i * 3] >> 3) | (p[i * 3 + 1] >> 3) << 5 | (p[i * 3 + 2] >> 3) << 10) for i in range(256)]
        _, ln = lz77(rom.d, bm, limit=0x20000)
        put_lz(rom, allrefs, bm, ln, idx)
        _, ln = lz77(rom.d, pl, limit=0x1000)
        put_lz(rom, allrefs, pl, ln, struct.pack('<256H', *cols))
    return {k: len(v['pieces']) for k, v in res.items()}
