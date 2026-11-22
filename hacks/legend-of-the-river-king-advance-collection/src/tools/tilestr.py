# Title menus and file-select panels. These are pre-drawn kana tiles placed by 16-bit tile strings
# (or a fixed LZ77 map), so each English label is rendered into its own run of tiles.
import struct
import font_en
from lzscan import lz77
from gfx import strip, to_tiles, shift
from namekbd import put_lz

def render(text, ntiles, ink=3, align='center', height=1):
    """Text in a ntiles x height tile area; returns tiles row-major."""
    w = sum(font_en.width(c) if c != ' ' else 3 for c in text) - 1
    px = strip(text, ntiles * 8)
    if ink != 3: px = [[ink if v == 3 else v for v in r] for r in px]
    dx = (ntiles * 8 - w) // 2 if align == 'center' else (ntiles * 8 - w - 2 if align == 'right' else 1)
    if dx > 0: px = shift(px, dx)
    if height == 2:
        # 16 px band: glyph rows 1-7 of the strip land on rows 4-10
        blank = [[1] * (ntiles * 8)]
        px = blank * 3 + px[1:] + blank * 6
        return to_tiles(px[:8]) + to_tiles(px[8:16])
    return to_tiles(px)

def ntiles(text):
    w = sum(font_en.width(c) if c != ' ' else 3 for c in text) - 1
    return max(1, -(-(w + 2) // 8))

# ---- game 3 file panel: 12 strings (16-bit tile ids, 0x00FF end), pointer table at 0x2013C4
G3_FILE = dict(block=0x1be5a4, ptrtab=0x2013c4, header=[0x1a, 0x1b, 0x1c, 0x1d],
               pool=list(range(0x1e, 0x3a)) + list(range(0x40, 0xd0)),
               texts=['Stream', 'Upper Lake', 'Creek', 'Plains Lake', 'Mirage Lake', 'HP', 'Yen', 'EXP',
                      'Time', 'cm', 'No data', 'Still an egg'])

def apply_g3_file(rom, allrefs):
    k = G3_FILE
    blk, ln = lz77(rom.d, k['block'], limit=0x10000)
    blk = bytearray(blk) + bytes(max(0, (max(k['pool']) + 1) * 32 - len(blk)))
    for t, tile in zip(k['header'], render('File', 4, align='right')):
        blk[t * 32:t * 32 + 32] = tile
    pool = list(k['pool'])
    for i, text in enumerate(k['texts']):
        n = ntiles(text)
        ids = [pool.pop(0) for _ in range(n)]
        for t, tile in zip(ids, render(text, n)):
            blk[t * 32:t * 32 + 32] = tile
        a = rom.put(b''.join(struct.pack('<H', t) for t in ids) + struct.pack('<H', 0xff), align=2)
        # code also points straight at some strings, so move every reference
        orig = struct.unpack_from('<I', rom.d, k['ptrtab'] + 4 * i)[0] - 0x08000000
        for ref in allrefs.get(orig, []):
            rom.w(ref, struct.pack('<I', 0x08000000 + a))
    used = max(t for t in k['pool'] if t not in pool) + 1
    put_lz(rom, allrefs, k['block'], ln, bytes(blk[:max(used, 0x40) * 32]))

# ---- game 3 title menu: fixed LZ77 map, three 6x2-tile labels (block 0x1BD5B0)
G3_TITLE = dict(block=0x1bd5b0, items=[
    ('Start', [0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57], 3),
    ('Uocchi', [0x48, 0x49, 0x4a, 0x4b, 0x4c, 0x4d, 0x58, 0x59, 0x5a, 0x5b, 0x5c, 0x5d], 3),
    ('Erase Data', [0x4e, 0x4f, 0x60, 0x61, 0x62, 0x63, 0x5e, 0x5f, 0x70, 0x71, 0x72, 0x73], 4),
    ('Erase Data', [0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x76, 0x77, 0x78, 0x79, 0x7a, 0x7b], 3),
])

def apply_g3_title(rom, allrefs):
    blk, ln = lz77(rom.d, G3_TITLE['block'], limit=0x10000)
    blk = bytearray(blk)
    for text, ids, ink in G3_TITLE['items']:
        for t, tile in zip(ids, render(text, 6, ink=ink, height=2)):
            blk[t * 32:t * 32 + 32] = tile
    put_lz(rom, allrefs, G3_TITLE['block'], ln, bytes(blk))

# ---- game 4 title menu (blocks 0xE3D34 / 0xE4E04, the same tiles in both) and brother choice.
# Menu streams: 16-bit tiles, F1 = next row, F0 = end. Main menu at 0x1FE5E6, brother choice at 0x1FE5B2.
G4_TITLE_BLOCKS = [0xe3d34, 0xe4e04]
G4_IN_PLACE = [('Start', [0x42, 0x43, 0x44, 0x45], 3), ('Erase Data', [0x46, 0x47, 0x48, 0x49, 0x4a, 0x4b], 3),
               ('Erase Data', [0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b], 4)]
G4_BRO = [('Little Bro', [0xc0, 0xc1, 0xc2, 0xc3, 0xc4, 0xc5]), ('Big Bro', [0xc6, 0xc7, 0xc8, 0xc9, 0xca, 0xcb])]

def apply_g4_title(rom, allrefs):
    for off in G4_TITLE_BLOCKS:
        blk, ln = lz77(rom.d, off, limit=0x10000)
        blk = bytearray(blk)
        for text, ids, ink in G4_IN_PLACE:
            for t, tile in zip(ids, render(text, len(ids), ink=ink, align='left')):
                blk[t * 32:t * 32 + 32] = tile
        for text, ids in G4_BRO:
            for t, tile in zip(ids, render(text, len(ids), align='left')):
                blk[t * 32:t * 32 + 32] = tile
        put_lz(rom, allrefs, off, ln, bytes(blk))
    BL = [0x10, 0x64, 0x64, 0x64, 0x64, 0x64]
    s = BL + [0xf1] + G4_BRO[0][1] + [0xf1] + BL + [0xf1] + G4_BRO[1][1] + [0xf0]
    a = rom.put(b''.join(struct.pack('<H', v) for v in s), align=2)
    for ref in allrefs.get(0x1fe5b2, []):
        rom.w(ref, struct.pack('<I', 0x08000000 + a))

# ---- game 4 file select (block 0xE5C54): ファイル header and the けいけん label (string 0x1FE760, 4 tiles)
def apply_g4_file(rom, allrefs):
    off = 0xe5c54
    blk, ln = lz77(rom.d, off, limit=0x10000)
    blk = bytearray(blk)
    for t, tile in zip([0x1a, 0x1b, 0x1c, 0x1d], render('File', 4, align='right')):
        blk[t * 32:t * 32 + 32] = tile
    exp = [0x38, 0x39, 0x3e, 0x3f]
    for t, tile in zip(exp, render('EXP', 4, align='left')):
        blk[t * 32:t * 32 + 32] = tile
    put_lz(rom, allrefs, off, ln, bytes(blk))
    assert struct.unpack_from('<5H', rom.d, 0x1fe760) == (0x32, 0x22, 0x32, 0x25, 0xf0)
    rom.w(0x1fe760, struct.pack('<4H', *exp))
