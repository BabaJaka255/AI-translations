# Graphics text in LZ77-compressed tile blocks: 体力 お金 命令 and the はい/いいえ choice tiles.
import pickle, struct
import font_en
from lzscan import lz77

def lz77_compress(data):
    """Plain GBA LZ77 (type 0x10) compressor, greedy with 4 KB window."""
    out = bytearray([0x10, len(data) & 0xff, (len(data) >> 8) & 0xff, (len(data) >> 16) & 0xff])
    i = 0; n = len(data)
    while i < n:
        flag_pos = len(out); out.append(0); flags = 0
        for b in range(8):
            if i >= n: break
            best_len, best_d = 0, 0
            lo = max(0, i - 4096)
            maxlen = min(18, n - i)
            # VRAM-safe: distance >= 2
            for j in range(i - 2, lo - 1, -1):
                l = 0
                while l < maxlen and data[j + l] == data[i + l]: l += 1
                if l > best_len:
                    best_len, best_d = l, i - j
                    if l == maxlen: break
            if best_len >= 3:
                flags |= 0x80 >> b
                d = best_d - 1
                out += bytes([((best_len - 3) << 4) | (d >> 8), d & 0xff])
                i += best_len
            else:
                out.append(data[i]); i += 1
        out[flag_pos] = flags
    while len(out) % 4: out.append(0)
    return bytes(out)

def strip(text, width):
    """Render text with font_en into a width x 8 pixel grid (ink 3, bg 1), art rows start at row 1."""
    px = [[1] * width for _ in range(8)]
    x = 0
    for ch in text:
        if ch == ' ': x += 3; continue
        rows = font_en.G[ch]
        for y, row in enumerate(rows):
            for k, c in enumerate(row):
                if c == '#' and x + k < width and y + 1 < 8: px[y + 1][x + k] = 3
        x += font_en.width(ch)
    return px

def art(rows):
    """Custom pixel art: list of 8 strings, '#' ink."""
    return [[3 if c == '#' else 1 for c in r.ljust(8)] for r in rows]

def to_tiles(px):
    w = len(px[0]); out = []
    for t in range(w // 8):
        b = bytearray()
        for y in range(8):
            for x in range(0, 8, 2):
                b.append(px[y][t * 8 + x] | px[y][t * 8 + x + 1] << 4)
        out.append(bytes(b))
    return out

def centered(text, ntiles):
    w = sum(font_en.width(c) for c in text) - 1
    pad = (ntiles * 8 - w) // 2
    return to_tiles(strip(' ' * 0 + text, ntiles * 8)) if pad <= 0 else to_tiles(shift(strip(text, ntiles * 8), pad))

def shift(px, dx):
    return [[1] * dx + row[:len(row) - dx] for row in px]

NO = art(['', '#  #    ', '## #    ', '# ##  # ', '#  # # #', '#  # # #', '#  #  # ', ''])

def replacements():
    pat = pickle.load(open('kanji_pat.pkl', 'rb'))
    hp = centered('HP', 2); yen = centered('Yen', 2); cmd = centered('Cmd', 2); yes = centered('Yes', 2)
    no = to_tiles(NO)
    kanji = {pat['tai']: hp[0], pat['ryoku']: hp[1], pat['o']: yen[0], pat['kane']: yen[1],
             pat['mei']: cmd[0], pat['rei']: cmd[1]}
    kana = {pat['ha']: yes[0], pat['i']: yes[1], pat['e']: no[0]}
    return kanji, kana

# blocks: offset -> which sets to replace
BLOCKS = {0xd3cf4: ('kanji', 'kana'), 0xd3f28: ('kana',), 0xe1448: ('kanji', 'kana'), 0xe2880: ('kanji', 'kana'),
          0xe5c54: ('kanji',), 0x16dd30: ('kanji',), 0xdda94: ('kanji',)}

# FF (yes/no) handler writes map entries: [f5 f6] .. [f6 f6 f7]; make it [f5 f6] .. [f7 ff ff]
CODE = [(0x45b40, struct.pack('<H', 0x880a), struct.pack('<H', 0x22f7)),
        (0x45b4c, struct.pack('<H', 0x880a), struct.pack('<H', 0x22ff)),
        (0x45b5e, struct.pack('<H', 0x880a), struct.pack('<H', 0x22ff))]

def apply(rom, allrefs):
    kanji, kana = replacements()
    sets = {'kanji': kanji, 'kana': kana}
    for off, which in BLOCKS.items():
        d, ln = lz77(rom.d, off, limit=0x10000)
        d = bytearray(d)
        for w in which:
            for old, new in sets[w].items():
                i = 0
                while True:
                    i = d.find(old, i)
                    if i < 0: break
                    if i % 32 == 0: d[i:i + 32] = new
                    i += 1
        c = lz77_compress(bytes(d))
        assert lz77(c + b'\0' * 8, 0, limit=0x10000)[0] == bytes(d)
        if len(c) <= ln:
            rom.w(off, c)
        else:
            a = rom.put(c, align=4)
            for ref in allrefs.get(off, []):
                rom.w(ref, struct.pack('<I', 0x08000000 + a))
    for off, old, new in CODE:
        assert bytes(rom.d[off:off + len(old)]) == old, hex(off)
        rom.w(off, new)
