# Game 4 menus: each menu is a 16-bit tile stream (rows of 8 map entries, 0xF1 = next row, 0xF0 = end)
# plus one label string the text engine renders into consecutive tiles starting at a base tile.
# The Japanese menus reuse tiles between words; for English every word gets its own tiles, padded to a
# tile boundary with '|' (PAD), and the stream is rebuilt to point at them.
import struct
import font_en

def tiles_of(word):
    if word in ('\u24c1', '\u24bc'): return 1
    px = sum(font_en.width(c) for c in word) - 1
    return (px + 7) // 8

# msg: label string ROM offset; base: first tile; W: tiles the print may use;
# stream: ROM offset of the 16-bit map stream; rows: per row (1..3, or 0 for the header) a list of (col, word)
# Words in 'bait' slot are drawn by another print (bait type, tiles given by 'extra').
MENUS = [
    dict(name='field cmd p1', msg=0x114e4, base=0xe0, W=11, stream=0x1f87d8,
         # Ⓛ / Ⓖ are one-tile 'Lv' and 'Go' glyphs; Go replaces Fish where the game says いどう (code below)
         words=['Fish', 'Eat', 'Bag', 'Gear', 'Ⓛ', 'Ⓖ'],
         rows={1: [(0, 'Fish'), (5, 'Eat')], 2: [(0, '#eb'), (5, 'Bag')], 3: [(0, 'Gear'), (5, 'Ⓛ')]},
         extra={'#eb': [0xeb, 0xec, 0xed]}),
    dict(name='field cmd p2', msg=0x114f3, base=0xe0, W=14, stream=0x1f8820,
         words=['Box', 'Net', 'Bugs', 'Pick', 'Pot', 'Dive'],
         rows={1: [(0, 'Box'), (5, 'Net')], 2: [(0, 'Bugs'), (5, 'Pick')], 3: [(0, 'Pot'), (5, 'Dive')]}),
    dict(name='tackle (fly)', msg=0x11504, base=0xe0, W=14, stream=0x1f8868,
         words=['Rod', 'Bait', 'Lure', 'Fly', 'Hook', 'Bag'],
         rows={1: [(0, 'Rod'), (4, 'Bait')], 2: [(0, 'Lure'), (4, 'Fly')], 3: [(0, 'Hook'), (4, 'Bag')]}),
    dict(name='tackle (jig)', msg=0x11515, base=0xe0, W=14, stream=0x1f88b0,
         words=['Rod', 'Bait', 'Lure', 'Jig', 'Hook', 'Bag'],
         rows={1: [(0, 'Rod'), (4, 'Bait')], 2: [(0, 'Lure'), (4, 'Jig')], 3: [(0, 'Hook'), (4, 'Bag')]}),
    dict(name='cooler space', msg=0x11529, base=0xe0, W=14, stream=0x1f88f8,
         words=['Cooler', 'Capacity', 'Total'],
         rows={0: [(1, 'Cooler')], 1: [(0, 'Capacity')], 3: [(0, 'Total')]},
         keep_header=True),
    dict(name='basket space', msg=0x1157a, base=0xe0, W=14, stream=None,
         words=['Storage', 'Capacity', 'Total']),
    dict(name='items/mail order', msg=0x11538, base=0xe0, W=14, stream=0x1f8940,
         words=['Items', 'Catalog'],
         rows={1: [(1, 'Items')], 2: [(1, 'Catalog')]}),
    dict(name='battle', msg=0x11542, base=0xc0, W=8, stream=0x1f8988,
         words=['Fight', 'Eat', 'Run'],
         rows={1: [(2, 'Fight')], 2: [(2, 'Eat')], 3: [(2, 'Run')]}),
    dict(name='flower', msg=0x1154d, base=0xe0, W=14, stream=0x1f89d0,
         words=['Pick', 'Water', 'Leave'],
         rows={1: [(1, 'Pick')], 2: [(1, 'Water')], 3: [(1, 'Leave')]}),
    dict(name='bug tree', msg=0x1155b, base=0xe0, W=14, stream=0x1f8a18,
         words=['Catch', 'Sap', 'Leave'],
         rows={1: [(1, 'Catch')], 2: [(1, 'Sap')], 3: [(1, 'Leave')]}),
    dict(name='flower bed', msg=0x11568, base=0xe0, W=14, stream=0x1f8a60,
         words=['Plant', 'Basket', 'Items'],
         rows={1: [(1, 'Plant')], 2: [(1, 'Basket')], 3: [(1, 'Items')]}),
]

# Code patches: (rom offset, old bytes, new bytes)
CODE = [
    # rod / hook shop title (strings B3E / B3F): printed on tiles 72-73 (W=2) and shown on cells 9-10;
    # now printed on the empty tiles 78-7B (W=4) and shown on cells 8-11, so 'Rods' and 'Hooks' fit
    (0x3ea32, bytes([0x72, 0x20]), bytes([0x78, 0x20])),
    (0x3eb2a, bytes([0x72, 0x20]), bytes([0x78, 0x20])),
    (0x3ea4c, struct.pack('<I', 0x0201), struct.pack('<I', 0x0401)),
    (0x3eb44, struct.pack('<I', 0x0201), struct.pack('<I', 0x0401)),
    (0x309a6, bytes([0xff, 0x21]), bytes([0x78, 0x21])),
    (0x309ac, bytes([0x72, 0x21]), bytes([0x79, 0x21])),
    (0x309b2, bytes([0x73, 0x21]), bytes([0x7a, 0x21])),
    (0x309b8, bytes([0xff, 0x21]), bytes([0x7b, 0x21])),
    # bait-type print in the field menu: tile 0xea W=4 -> tile 0xeb W=3
    # いどう (move) in the first field command: tiles F6 E2 E3 -> Go (EA) and two blanks
    (0x3967e, bytes([0xf6, 0x23]), bytes([0xea, 0x23])),
    (0x3969a, bytes([0xe2, 0x23]), bytes([0xff, 0x23])),
    (0x396b6, bytes([0xe3, 0x23]), bytes([0xff, 0x23])),
    (0x395bc, bytes([0xea, 0x20]), bytes([0xeb, 0x20])),
    (0x39644, struct.pack('<I', 0x0401), struct.pack('<I', 0x0301)),
    # the same print again when a window (gear, ...) redraws the field panel
    (0x3e322, bytes([0xea, 0x20]), bytes([0xeb, 0x20])),
    (0x3e370, struct.pack('<I', 0x0401), struct.pack('<I', 0x0301)),
    # field menu label print W=10 -> 11 (literal 0x0a01)
    (0x3964c, struct.pack('<I', 0x0a01), struct.pack('<I', 0x0b01)),
    # flower/bug basket title: the game blanked one tile to show 花かご or 虫かご; keep the stream title as is
    (0x39812, bytes([0xfd, 0x23]), bytes([0xe0, 0x23])),
    (0x39886, bytes([0xfd, 0x23]), bytes([0xe0, 0x23])),
    (0x398a2, bytes([0xe0, 0x23]), bytes([0xe1, 0x23])),
]

def label(m):
    return '|'.join(m['words']) + '|{f0}'

def assign(m):
    pos = {}
    t = m['base']
    for w in m['words']:
        n = tiles_of(w)
        pos[w] = list(range(t, t + n))
        t += n
    assert t - m['base'] <= m['W'], (m['name'], t - m['base'], m['W'])
    pos.update(m.get('extra', {}))
    return pos

def read_stream(rom, off):
    rows = [[]]
    o = off
    while True:
        h = struct.unpack_from('<H', rom, o)[0]; o += 2
        if h == 0xf0: break
        if h == 0xf1: rows.append([]); continue
        rows[-1].append(h)
    return rows, o - off

def build_stream(rom, m):
    rows, ln = read_stream(rom, m['stream'])
    pos = assign(m)
    label_tiles = set(range(m['base'], m['base'] + 16))
    new = []
    for ri, row in enumerate(rows):
        if ri == 0:
            nr = list(row)
            for k in range(len(nr) - 2):
                if nr[k:k + 3] == [0xee, 0xff, 0xef]: nr[k:k + 3] = [0xee, 0xef, 0xff]
            if ri in m['rows']:
                for col, w in m['rows'][ri]:
                    for k, t in enumerate(pos[w]): nr[col + k] = t
            new.append(nr); continue
        # strip old label tiles (and the fixed は tile) to blank 0xff, keep borders
        nr = [0xff if ((e & 0x3ff) in label_tiles or e == 0xf5) else e for e in row]
        for col, w in m['rows'].get(ri, []):
            ts = pos[w]
            assert col + len(ts) <= len(nr), (m['name'], w)
            for k, t in enumerate(ts): nr[col + k] = t
        new.append(nr)
    out = bytearray()
    for i, row in enumerate(new):
        if i: out += struct.pack('<H', 0xf1)
        for e in row: out += struct.pack('<H', e)
    out += struct.pack('<H', 0xf0)
    assert len(out) == ln, (m['name'], len(out), ln)
    return bytes(out)

def apply(rom):
    """rom: bytearray. Writes streams and code patches; returns {msg_offset: label text}."""
    labels = {}
    for m in MENUS:
        assign(m)
        labels[m['msg']] = label(m)
        if m.get('stream') is not None:
            rom[m['stream']:m['stream'] + len(build_stream(rom, m))] = build_stream(rom, m)
    for off, old, new in CODE:
        assert bytes(rom[off:off + len(old)]) == old, hex(off)
        rom[off:off + len(new)] = new
    return labels

if __name__ == '__main__':
    r = bytearray(open('../rom/k34.gba', 'rb').read())
    for m in MENUS:
        print(m['name'], {w: [hex(t) for t in ts] for w, ts in assign(m).items()})
    apply(r)
    for m in MENUS:
        if m.get('stream'):
            rows, _ = read_stream(r, m['stream'])
            print(m['name']); [print('   ', ' '.join('%02x' % e for e in row)) for row in rows]
