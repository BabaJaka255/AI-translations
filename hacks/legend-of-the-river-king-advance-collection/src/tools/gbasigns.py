# Building signboards in both games: 釣 (tackle shop) -> a hook, 魚 (fish shop) -> a fish, 宿 -> INN, the same
# pictures as the Umi no Nushi and Shizen-ha patches, and 万 (general store, game 4) -> a shopping bag. The
# 2x2-tile signs sit in the field tilesets (4 in game 3, 13 in game 4), so each copy is found by content and
# redrawn in place.
from lzscan import lz77
from namekbd import put_lz

# Umi no Nushi plaque art (UmiToolkit/build/field_signs.py), 12x12
UMI_ART = {
    'tackle': ["     ###    ", "     # #    ", "     ###    ", "      #     ", "      #     ", "      #     ",
               " #    #     ", " ##   #     ", " #    #     ", " #   #      ", "  ###       ", "            "],
    'fish': ["            ", "            ", "            ", "     ###    ", " #  ######  ", " ########## ",
             " ####### ###", " ########## ", " #  ######  ", "     ###    ", "            ", "            "],
    'inn': ["            ", "            ", "            ", " # #  # #  #", " # ## # ## #", " # ## # ## #",
            " # # ## # ##", " # # ## # ##", " # #  # #  #", "            ", "            ", "            "],
    'store': ["            ", "    ####    ", "   #    #   ", "   #    #   ", " ########## ", " #        # ",
              " #        # ", " #        # ", " #        # ", " #        # ", " ########## ", "            "],
}
# name: (tiles in game 4 set 0x104DC4 as [[top-left, top-right], [bottom-left, bottom-right]], picture)
SIGNS = {'tackle': ([[0xae, 0xaf], [0x18, 0x19]], 'tackle'), 'fish': ([[0xac, 0xad], [0x14, 0x15]], 'fish'),
         'inn': ([[0xaa, 0xab], [0x10, 0x11]], 'inn'), 'store': ([[0xa8, 0xa9], [0x0c, 0x0d]], 'store')}
SOURCE = 0x104dc4
SETS = [0x104dc4, 0x1063bc, 0x1091fc, 0x10a70c, 0x10d65c, 0x10ebd4, 0x111b9c, 0x112fe4, 0x115d68, 0x1172a8,
        0x119f80, 0x11e0b8, 0x11f6f8, 0x1c1df8, 0x1c46e4, 0x1c7174, 0x1ca0f4]
BG, INK = 0xc, 0x6       # sign face and lettering colours (palette 3)
X0, Y0 = 2, 2            # 12x12 face inside the frame

def dec(t):
    return [[(t[y * 4 + x // 2] >> (4 * (x & 1))) & 15 for x in range(8)] for y in range(8)]

def enc(px):
    return bytes(px[y][x] | (px[y][x + 1] << 4) for y in range(8) for x in range(0, 8, 2))

def new_tiles(src):
    """{original tile bytes: new tile bytes}"""
    rep = {}
    for tiles, art in SIGNS.values():
        g = [[0] * 16 for _ in range(16)]
        for r, row in enumerate(tiles):
            for c, n in enumerate(row):
                for y, line in enumerate(dec(src[n * 32:n * 32 + 32])): g[r * 8 + y][c * 8:c * 8 + 8] = line
        for y, line in enumerate(UMI_ART[art]):
            for x, ch in enumerate(line): g[Y0 + y][X0 + x] = INK if ch == '#' else BG
        for r, row in enumerate(tiles):
            for c, n in enumerate(row):
                rep[bytes(src[n * 32:n * 32 + 32])] = enc([g[r * 8 + y][c * 8:c * 8 + 8] for y in range(8)])
    return rep

def apply(rom, allrefs):
    src, _ = lz77(rom.d, SOURCE, limit=0x10000)
    rep = new_tiles(src)
    done = 0
    for off in SETS:
        blk, ln = lz77(rom.d, off, limit=0x10000)
        blk = bytearray(blk); n = 0
        for t in range(len(blk) // 32):
            k = bytes(blk[t * 32:t * 32 + 32])
            if k in rep: blk[t * 32:t * 32 + 32] = rep[k]; n += 1
        assert n >= 8, (hex(off), n)       # every set has at least the tackle and fish signs
        put_lz(rom, allrefs, off, ln, bytes(blk)); done += n
    return done
