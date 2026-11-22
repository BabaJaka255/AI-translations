# Game 3 sub-windows (Food, Bait, Items, Gear, Creel). Each window loads its own 128-tile set at tile 0 with
# the kana it needs; names are 16-bit tile strings (0xFF end) in pointer tables, titles sit in the LZ77 map.
# English: every name is drawn into its own tile run, reusing the set's kana tiles and empty tiles.

import struct
from lzscan import lz77
from namekbd import put_lz
from tilestr import render
import ocr

KEEP_CHARS = set('0123456789〜')

WINDOWS = {
    'food': dict(block=0x1b8e80, maps=[0x1b92c8], blank=0x0a,
                 titles=[([0x0b, 0x0c, 0x0d], 'Food')],
                 tables={0x1ff870: ['Mandarin', 'Rice Ball', 'Bento']}),
    'bait': dict(block=0x1b7124, maps=[0x1b7644, 0x1f7b44], blank=0x37, fixed=[([0x7f], '\u00a5')],
                 titles=[([0x14, 0x15], 'Bait')],
                 tables={0x1fef90: ['Worms', 'Maggots', 'Insects', 'Bloodworm', 'Stream Bug', 'Paste Bait',
                                    'Small Fish', 'Frog']}),
    'items': dict(block=0x1b9370, maps=[0x1b9aec], blank=0x0a,
                  titles=[([0x0b, 0x0c, 0x0d], 'Items')],
                  tables={0x1ff9e0: ['Creel S', 'Creel M', 'Creel L', 'Fishing Memo', 'Chum', 'Net', 'Washtub',
                                     'Pickaxe', 'Axe', 'Charm', 'Teacup', 'Charcoal', 'Wind Chime']}),
    # gear, lure, fly and bait sets double as the shop windows: the shop code draws the item icons
    # straight into the map (gear 30-76, lure/fly 10-4F as two 16x2 rows), and 7F is the price unit 円
    'gear': dict(block=0x1b86d4, maps=[0x1b8d0c, 0x1b8de0], blank=0x10, keep=range(0x30, 0x77),
                 fixed=[([0x7f], '\u00a5')],
                 code_titles={'rod': 'Rods', 'hook': 'Hooks'},
                 titles=[],
                 tables={0x1ff3cc: ['Float', 'Casting', 'Lure', 'Fly'],
                         0x1ff408: ['Rod', 'Float', 'Hook'],
                         # pieces are tile runs shared between names: 'Lure|Rod| S' = Lure + Rod + ' S'
                         0x1ff784: ['Pole S', 'Pole L', 'Casting|Rod| S', 'Casting|Rod| L',
                                    'Lure|Rod| S', 'Lure|Rod| L', 'Fly|Rod| S', 'Fly|Rod| L', 'Float', 'Sinker', '',
                                    'Pole S', 'Pole S', 'Pole S', 'Pole S', 'Pole S',
                                    'Hook| S', 'Hook| M', 'Hook| L', 'Hook| L', 'Hook']}),
    # lure and fly lists (window table entries 8 and 9): 64-tile sets, names at tiles 50+
    'lure': dict(block=0x1b77a0, maps=[0x1b7e08], blank=0x0d, keep=range(0x10, 0x50), fixed=[([0x7f], '\u00a5')],
                 titles=[([0x0a, 0x0b, 0x0c], 'Lures')],
                 tables={0x1ff0c8: ['Spinner', 'Spinnerbait', 'Minnow', 'Crankbait', 'Popper', 'Spoon', 'Rubber Worm',
                                    'Frog Lure']}),
    'fly': dict(block=0x1b7f64, maps=[0x1b8570], blank=0x0d, keep=range(0x10, 0x50), fixed=[([0x7f], '\u00a5')],
                titles=[([0x0a, 0x0b, 0x0c], 'Flies')],
                tables={0x1ff2a4: ['Mayfly| (Wet)', 'Mayfly| (Dry)', 'Caddis| (Wet)', 'Caddis| (Dry)', 'Diptera| (Wet)',
                                   'Diptera| (Dry)', 'Stonefly| (Wet)', 'Stonefly| (Dry)']}),
    # tackle shop "Items" counter: its own set; icons are drawn by code from the '?' tiles
    'shopitems': dict(block=0x1b9be0, maps=[0x1ba1d4], blank=0x0a, fixed=[([0x3e], '\u00a5')],
                      titles=[([0x0b, 0x0c, 0x0d], 'Items')],
                      tables={0x1ffaf8: ['Mandarin', 'Rice Ball', 'Bento', 'Creel M', 'Creel L', 'Chum', 'Net']}),
    # fish shop price board (ねたん): size bands and the price per band
    'prices': dict(block=0x1ba770, maps=[0x1baba4], blank=0x0a, fixed=[([0x24], '\u00a5')],
                   titles=[([0x0c, 0x0d, 0x0e], 'Prices'), ([0x10, 0x0f, 0x11, 0x12], 'Total')],
                   tables={}),
    'creel': dict(block=0x1ba27c, maps=[0x1ba684], blank=0x0a, erase=[0x13, 0x24], erase_with=0x0a,
                  titles=[([0x0c, 0x0d, 0x0e, 0x0f, 0x0d], 'Capacity'), ([0x10, 0x0d, 0x11, 0x12], 'Total')],
                  tables={}),
}

def ntiles(text):
    import font_en
    return max(1, -(-(sum(font_en.width(c) if c != ' ' else 3 for c in text)) // 8))

def maps_of(rom, w):
    out = []
    for m in w['maps']:
        d, ln = lz77(rom.d, m, limit=0x10000)
        out.append((m, ln, list(struct.unpack('<%dH' % (len(d) // 2), d))))
    return out

def apply_window(rom, allrefs, w):
    blk, bln = lz77(rom.d, w['block'], limit=0x10000)
    blk = bytearray(blk)
    kana = ocr.read_block(w['block'], 'g3')
    maps = maps_of(rom, w)
    title_ids = {t for ids, _ in w['titles'] for t in ids}
    in_maps = {v & 0x3ff for _, _, hw in maps for v in hw}
    protect = (in_maps - title_ids) | {t for t, c in kana.items() if c == '?' or c in KEEP_CHARS}
    protect |= set(w.get('keep', ())) | {t for ids, _ in w.get('fixed', []) for t in ids}
    if w['blank'] is not None: protect.add(w['blank'])
    free = [t for t in range(len(blk) // 32) if t not in protect]
    def take(n):
        assert len(free) >= n, (w['block'], n, len(free))
        ids = free[:n]; del free[:n]
        return ids
    seen = {}
    if w['blank'] is not None:
        seen[bytes(blk[w['blank'] * 32:w['blank'] * 32 + 32])] = w['blank']
    def place(text, n, align='left'):
        # identical tiles (blank ends, shared word starts like 'Lure Rod S' / 'Lure Rod L') are stored once
        ids = []
        for tile in render(text, n, align=align):
            tile = bytes(tile)
            if tile not in seen:
                t = take(1)[0]
                blk[t * 32:t * 32 + 32] = tile
                seen[tile] = t
            ids.append(seen[tile])
        return ids
    for ids, word in w.get('fixed', []):
        for t, tile in zip(ids, render(word, len(ids))):
            blk[t * 32:t * 32 + 32] = bytes(tile)
    # titles the shop code writes into row 1, cells 8-11 (see SHOP_TITLE_CODE)
    w['_code_titles'] = {k: place(word, 4, 'center') for k, word in w.get('code_titles', {}).items()}
    # titles in the map: same number of cells, padded with the map's own blank
    for t in w.get('erase', []):          # e.g. the 尾 counter after the creel counts
        blk[t * 32:t * 32 + 32] = blk[w['erase_with'] * 32:w['erase_with'] * 32 + 32]
    for ids, word in w['titles']:
        n = ntiles(word)
        assert n <= len(ids), (word, ids)
        new = place(word, n)
        for m in maps:
            hw = m[2]
            for i in range(len(hw) - len(ids) + 1):
                if [v & 0x3ff for v in hw[i:i + len(ids)]] == ids:
                    pad = hw[i - 1] & 0x3ff
                    for k in range(len(ids)):
                        hw[i + k] = (hw[i + k] & 0xfc00) | (new[k] if k < n else pad)
    # name tables: one tile run per distinct piece ('Lure Rod| S' = 'Lure Rod' run + ' S' run, so the size
    # letters are shared), every name padded to the longest in its table
    for tab, names in w['tables'].items():
        al = w.get('align', {}).get(tab, 'left')
        # 'Mayfly|(Wet)': each piece gets its own tile run, so shared pieces are stored once
        seqs = [sum((place(p, ntiles(p), al) for p in name.split('|')), []) if name else [] for name in names]
        width = max(len(q) for q in seqs)
        for i, q in enumerate(seqs):
            s = q + [w['blank']] * (width - len(q))
            orig = struct.unpack_from('<I', rom.d, tab + 4 * i)[0] - 0x08000000
            a = rom.put(b''.join(struct.pack('<H', v) for v in s) + b'\xff\x00', align=2)
            rom.w(tab + 4 * i, struct.pack('<I', 0x08000000 + a))
            for ref in allrefs.get(orig, []):
                if not (tab <= ref < tab + 4 * len(names)): rom.w(ref, struct.pack('<I', 0x08000000 + a))
    put_lz(rom, allrefs, w['block'], bln, bytes(blk))
    for m, ln, hw in maps:
        put_lz(rom, allrefs, m, ln, struct.pack('<%dH' % len(hw), *hw))
    return len(free)

# Rod and hook shops share map 1B8DE0; the shop code writes a 2-cell title (サオ / ハリ) with two strh.
# Each branch becomes ldr r0,=0x600D850 / ldr r1,=title / ldmia r1!,{r2,r3} / stmia r0!,{r2,r3} / b out,
# so four cells (32 px) come from a 4-halfword string. r2 and r3 are dead (the function returns next).
SHOP_TITLE_CODE = {
    'rod': dict(at=0x86968, lit=(0x869a0, 0x869a4),
                code=[0x480d, 0x490e, 0xc90c, 0xc00c, 0xe028]),
    'hook': dict(at=0x869b8, lit=(0x869cc, 0x869d0),
                 code=[0x4804, 0x4905, 0xc90c, 0xc00c, 0xe000]),
}
SHOP_TITLE_OLD = {'rod': bytes.fromhex('0d481c2101800d481d210180'), 'hook': bytes.fromhex('04481f21018004481621')}

def apply_shop_titles(rom, ids):
    for k, c in SHOP_TITLE_CODE.items():
        old = SHOP_TITLE_OLD[k]
        assert rom.d[c['at']:c['at'] + len(old)] == old, (k, rom.d[c['at']:c['at'] + 12].hex())
        a = rom.put(struct.pack('<4H', *ids[k]), align=4)
        rom.w(c['lit'][0], struct.pack('<I', 0x0600d850))
        rom.w(c['lit'][1], struct.pack('<I', 0x08000000 + a))
        rom.w(c['at'], struct.pack('<%dH' % len(c['code']), *c['code']))

def apply(rom, allrefs):
    left = {k: apply_window(rom, allrefs, w) for k, w in WINDOWS.items()}
    apply_shop_titles(rom, WINDOWS['gear']['_code_titles'])
    return left
