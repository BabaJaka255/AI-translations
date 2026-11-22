# Game 4 memo books (Items > Fish / Shell / Bug / Flower Memo).
# Fish Memo: set 0xE0368 (map 0xE090C), labels 最高 / 基本 / 総数 are 3x2 tiles in ink 10 on 14, 尾 is tile 1D;
#   the 大物 stamp is OBJ set 0xE12F8 (32x16, top row tiles 00-03, bottom row 10-13, solid red = 1).
# Shell / Bug / Flower Memo share set 0xE0AE8 (map 0xE1150): 価値 and 総数 labels, ランク (40-42) after the
#   rank letter, the counters 個 / 匹 / 本 are 2x2 tiles written by code, and the note すいそうに、おくことができる！
#   is a 2-row tile stream at 0x1FE540 (tiles 66-6F, 4D-4F, 5D-5E, 08 is the shared blank).
import struct
from lzscan import lz77
from namekbd import put_lz
from tilestr import render
from g3uo import stamp_tiles, recolour

FISH = dict(block=0xe0368, labels=[('Best', [0x50, 0x51, 0x52, 0x60, 0x61, 0x62]),
                                   ('Size', [0x53, 0x54, 0x55, 0x63, 0x64, 0x65]),
                                   ('Total', [0x56, 0x57, 0x58, 0x66, 0x67, 0x68])],
            erase=[0x1d])
STAMP = dict(block=0xe12f8, text='Big One', tiles=[0x00, 0x01, 0x02, 0x03, 0x10, 0x11, 0x12, 0x13], ink=1)
SHARED = dict(block=0xe0ae8, labels=[('Value', [0x50, 0x51, 0x52, 0x60, 0x61, 0x62]),
                                     ('Total', [0x53, 0x54, 0x55, 0x63, 0x64, 0x65])],
              rank=(' Rank', [0x40, 0x41, 0x42]),
              erase=[0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x48, 0x56, 0x57],
              note=[('You can put', [0x66, 0x67, 0x68, 0x69, 0x6a, 0x6b, 0x6c, 0x6d]),
                    ('it in a tank!', [0x6e, 0x6f, 0x4d, 0x4e, 0x4f, 0x5d, 0x5e])])
NOTE_STREAM = 0x1fe540
INK = 10

def bg_of(tile):
    n = [0] * 16
    for b in tile:
        n[b & 15] += 1; n[b >> 4] += 1
    return n.index(max(n))

def labels(blk, items):
    for text, ids in items:
        # the numbers sit on the lower tile row, so the word goes there and the upper row is cleared
        bg = bg_of(blk[ids[0] * 32:ids[0] * 32 + 32])
        for t, tile in zip(ids, [b'\x11' * 32] * 3 + render(text, 3)):
            blk[t * 32:t * 32 + 32] = recolour(bytes(tile), {1: bg, 3: INK})

def erase(blk, ids):
    # copy the set's own blank page tile (08): the counters are mostly ink, so their own colours can't tell
    for t in ids:
        blk[t * 32:t * 32 + 32] = blk[0x08 * 32:0x09 * 32]

def apply(rom, allrefs):
    blk, ln = lz77(rom.d, FISH['block'], limit=0x10000)
    blk = bytearray(blk)
    labels(blk, FISH['labels']); erase(blk, FISH['erase'])
    put_lz(rom, allrefs, FISH['block'], ln, bytes(blk))

    blk, ln = lz77(rom.d, STAMP['block'], limit=0x10000)
    blk = bytearray(blk)
    m = {4: STAMP['ink']}
    for t, tile in zip(STAMP['tiles'], stamp_tiles(STAMP['text'])):
        blk[t * 32:t * 32 + 32] = recolour(tile, m)
    put_lz(rom, allrefs, STAMP['block'], ln, bytes(blk))

    blk, ln = lz77(rom.d, SHARED['block'], limit=0x10000)
    blk = bytearray(blk)
    labels(blk, SHARED['labels'])
    text, ids = SHARED['rank']
    bg = bg_of(blk[ids[0] * 32:ids[0] * 32 + 32])
    for t, tile in zip(ids, render(text, 3, align='left')):
        blk[t * 32:t * 32 + 32] = recolour(bytes(tile), {1: bg, 3: INK})
    erase(blk, SHARED['erase'])
    for text, ids in SHARED['note']:
        for t, tile in zip(ids, render(text, len(ids), align='left')):
            blk[t * 32:t * 32 + 32] = tile
    put_lz(rom, allrefs, SHARED['block'], ln, bytes(blk))
    # second note row: drop the blank cell after が so the seven tiles run on
    row2 = [0x6e, 0x6f, 0x4d, 0x4e, 0x4f, 0x5d, 0x5e, 0x08]
    rom.w(NOTE_STREAM + 18, b''.join(struct.pack('<H', 0x1000 | t) for t in row2))
