# Game 4 sub-windows. Food, Bait and Items share one LZ77 map (0xDAFD8) whose title cells are tiles 0A-0D, so
# each window's own 128-tile set gets its English title drawn in place on 0A-0C. The level window (set 0xDDA94,
# map 0xDDE90) has its labels as pre-drawn kana tiles too.
import struct
from lzscan import lz77
from namekbd import put_lz
from tilestr import render

TITLES = {0xdc6b4: 'Food', 0xda9c4: 'Bait', 0xdcb10: 'Items'}
TITLE_TILES = [0x0a, 0x0b, 0x0c]

# shop windows (set tables 0x1F82A0 / 0x1F82E0, maps 0x1F8320): same title cells; the rod and hook set 0xDBEEC
# gets its title cells from code. Tile 7F of every shop set is the price unit 円.
# 0xDF40C is the fly counter's set in one brother's game (キジバリ, pheasant-feather flies)
SHOP_TITLES = {0xdb1a0: ([0x0a, 0x0b, 0x0c], 'Lures'), 0xdb880: ([0x0a, 0x0b, 0x0c], 'Flies'),
               0xdf40c: ([0x0a, 0x0b, 0x0c, 0x0d], 'Flies'), 0xdd580: ([0x0a, 0x0b, 0x0c], 'Items'),
               0xdfc20: ([0x0a, 0x0b, 0x0c, 0x0d], 'Catalog')}
YEN_SETS = [0xdbeec, 0xdb1a0, 0xda9c4, 0xdb880, 0xdf40c, 0xdd580, 0xdcb10, 0xdc6b4]
# fish shop price board (set 0xDDF88, map 0xDE3EC): ねたん, こうけい, 円 drawn in place
PRICES = dict(block=0xddf88, labels=[([0x0c, 0x0d, 0x0e], 'Prices'), ([0x10, 0x0f, 0x11, 0x12], 'Total'),
                                     ([0x24], '\u00a5')])

LEVEL = dict(block=0xdda94, map=0xdde90, blank=0x0a,
             # (row, col, tiles, text, align)
             labels=[(1, 6, list(range(0x10, 0x19)), 'Level', 'center'),
                     (7, 3, list(range(0x20, 0x25)), 'EXP', 'left'),
                     (9, 3, list(range(0x25, 0x2d)), 'Fish Caught', 'left'),
                     (11, 3, list(range(0x30, 0x3a)), 'To Next Level', 'left')],
             erase=[0x1c, 0x1d])                 # 尾 after the fish count (8x16 kanji)

# cooler / bug cage / flower basket window (set 0xDE650): the title is a tiny F0-ended tile stream the code
# writes at row 1, col 4 (0x1F8AA8 クーラー, 0x1F8AB2 虫かご, 0x1F8ABA 花かご). Tiles 19-1F are unused; 0A, 16 and
# 17 also spell ランク elsewhere, so they stay.
BASKET = dict(block=0xde650, titles=[(0x1f8aa8, 'Cooler', [0x19, 0x1a, 0x1b, 0x1c]),
                                     (0x1f8ab2, 'Bug Cage', [0x1d, 0x1e, 0x1f, 0x08, 0x09]),
                                     (0x1f8aba, 'Flowers', [0x0d, 0x0e, 0x0f, 0x10])])

def _put(blk, ids, tiles):
    for t, tile in zip(ids, tiles):
        blk[t * 32:t * 32 + 32] = tile

def apply(rom, allrefs):
    # one decompress / recompress per set: put_lz may move a set, so a second pass would read the old copy
    for off in set(TITLES) | set(SHOP_TITLES) | set(YEN_SETS):
        blk, ln = lz77(rom.d, off, limit=0x10000)
        blk = bytearray(blk)
        if off in TITLES:
            _put(blk, TITLE_TILES, render(TITLES[off], len(TITLE_TILES), align='center'))
        if off in SHOP_TITLES:
            ids, word = SHOP_TITLES[off]
            _put(blk, ids, render(word, len(ids), align='center'))
        if off in YEN_SETS:
            _put(blk, [0x7f], render('\u00a5', 1))
        put_lz(rom, allrefs, off, ln, bytes(blk))
    P = PRICES
    blk, ln = lz77(rom.d, P['block'], limit=0x10000)
    blk = bytearray(blk)
    for ids, word in P['labels']:
        _put(blk, ids, render(word, len(ids), align='center'))
    put_lz(rom, allrefs, P['block'], ln, bytes(blk))
    B = BASKET
    blk, ln = lz77(rom.d, B['block'], limit=0x10000)
    blk = bytearray(blk)
    for stream, word, ids in B['titles']:
        _put(blk, ids, render(word, len(ids), align='left'))
        a = rom.put(b''.join(struct.pack('<H', t) for t in ids + [0xf0]), align=2)
        for ref in allrefs.get(stream, []):
            rom.w(ref, struct.pack('<I', 0x08000000 + a))
    put_lz(rom, allrefs, B['block'], ln, bytes(blk))
    L = LEVEL
    blk, ln = lz77(rom.d, L['block'], limit=0x10000)
    blk = bytearray(blk)
    m, mln = lz77(rom.d, L['map'], limit=0x10000)
    hw = list(struct.unpack('<%dH' % (len(m) // 2), m))
    for r, c, ids, text, al in L['labels']:
        _put(blk, ids, render(text, len(ids), align=al))
        for k, t in enumerate(ids):              # the Japanese shares one ヘ tile between two labels
            i = r * 32 + c + k
            hw[i] = (hw[i] & 0xfc00) | t
    b = L['blank']
    for t in L['erase']:
        blk[t * 32:t * 32 + 32] = blk[b * 32:b * 32 + 32]
    put_lz(rom, allrefs, L['block'], ln, bytes(blk))
    put_lz(rom, allrefs, L['map'], mln, struct.pack('<%dH' % len(hw), *hw))
