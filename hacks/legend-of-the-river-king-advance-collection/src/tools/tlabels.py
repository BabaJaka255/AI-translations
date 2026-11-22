# Label rewriting for screens whose words are pre-drawn kana tiles placed by an LZ77 map.
# A label is (row, col, cells, text, align): the cells are refilled with the text, using the tiles the Japanese
# had in those cells first and then the set's spare tiles (all colour 0 and not in any map), deduplicated.
import struct
from lzscan import lz77
from namekbd import put_lz
from tilestr import render

def apply(rom, allrefs, block, maps, labels, keep=(), width=32, blank=None, fixed=()):
    """fixed: (tile ids, text, align) drawn in place, for words the code places itself."""
    blk, bln = lz77(rom.d, block, limit=0x10000)
    blk = bytearray(blk)
    for ids, text, al in fixed:
        for t, tile in zip(ids, render(text, len(ids), align=al)):
            blk[t * 32:t * 32 + 32] = tile
    keep = set(keep) | {t for ids, _, _ in fixed for t in ids}
    ms = []
    for m in maps:
        d, ln = lz77(rom.d, m, limit=0x10000)
        ms.append([m, ln, list(struct.unpack('<%dH' % (len(d) // 2), d))])
    hw0 = ms[0][2]
    in_maps = {v & 0x3ff for _, _, hw in ms for v in hw}
    n = len(blk) // 32
    spare = [t for t in range(n) if t not in in_maps and t not in keep and not any(blk[t * 32:t * 32 + 32])]
    own = []
    for r, c, cells, text, al in labels:
        for k in range(cells):
            t = hw0[r * width + c + k] & 0x3ff
            if t != blank and t not in keep and t not in own: own.append(t)
    # a label tile shared with a cell outside every label must not be redrawn
    lab_cells = {(r * width + c + k) for r, c, cells, _, _ in labels for k in range(cells)}
    for _, _, hw in ms:
        for i, v in enumerate(hw):
            if i not in lab_cells and (v & 0x3ff) in own: own.remove(v & 0x3ff)
    pool = own + spare
    seen = {}
    if blank is not None: seen[bytes(blk[blank * 32:blank * 32 + 32])] = blank
    for r, c, cells, text, al in labels:
        tiles = render(text, cells, align=al) if text else [bytes(blk[blank * 32:blank * 32 + 32])] * cells
        for k, tile in enumerate(tiles):
            tile = bytes(tile)
            if tile not in seen:
                assert pool, ('out of tiles', hex(block), text)
                t = pool.pop(0); blk[t * 32:t * 32 + 32] = tile; seen[tile] = t
            for _, _, hw in ms:
                i = r * width + c + k
                hw[i] = (hw[i] & 0xfc00) | seen[tile]
    put_lz(rom, allrefs, block, bln, bytes(blk))
    for m, ln, hw in ms:
        put_lz(rom, allrefs, m, ln, struct.pack('<%dH' % len(hw), *hw))
    return len(pool)
