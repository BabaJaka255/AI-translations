"""Menus for the English build: name keyboard, End buttons, and (later) 16 px menu labels.
Name entry ($00:D64C) stores the code from the table at $00:D67F (ROM 0x567F, index = cursor $0AA6, 16 per row) into
the name sprites; the codes are 8x8 font codes, so names show in the English font. The keyboard itself is drawn by the
name entry tilemap at ROM 0xA0000 (column-major): top block rows 6+2r, lower block rows 17+2(r-5), cols 7+2c.
Valid cells (cursor shape is unchanged): rows 0-4 have 9 columns, row 5 has 7, rows 6-9 have 6."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from build_font import ENC
KEYS = ['ABCDEFGHI', 'JKLMNOPQR', 'STUVWXYZ-', 'abcdefghi', 'jklmnopqr',
        'stuvwxy', 'z.!?\'&', '012345', '6789()', ',:~*/%']
SHAPE = [9, 9, 9, 9, 9, 7, 6, 6, 6, 6]
NAME_MAP, DATE_MAP, NAME_TBL = 0xA0000, 0xC4000, 0x567F
def put_map(r, m, row, col, word):
    i = col*32 + row; r[m + 2*i] = word & 0xFF; r[m + 2*i + 1] = word >> 8
def patch_keyboard(r):
    for k, (keys, n) in enumerate(zip(KEYS, SHAPE)):
        assert len(keys) == n, keys
        for c, ch in enumerate(keys):
            code = ENC[ch]
            r[NAME_TBL + 16*k + c] = code
            row = 6 + 2*k if k < 5 else 17 + 2*(k - 5)
            put_map(r, NAME_MAP, row, 7 + 2*c, 0x100 + code)
            if k: put_map(r, NAME_MAP, row - 1, 7 + 2*c, 0)     # clear any dakuten above (row 5 is the frame)
    # End buttons: name entry row 25 cols 27-29, date entry row 24 cols 13-17 (was お_わ_り)
    for j, ch in enumerate('End'): put_map(r, NAME_MAP, 25, 27 + j, 0x100 + ENC[ch])
    for j, ch in enumerate(' End '): put_map(r, DATE_MAP, 24, 13 + j, 0x100 + (0 if ch == ' ' else ENC[ch]) if ch != ' ' else 0)

# ---------------------------------------------------------------------------------------------------------------
# 16 px menu labels. The menu screens are column-major BG maps over the glyph sheet at ROM 0x3A000 (VRAM tiles
# 000-0FF, palette 0; colour 1 = box fill, F = text). English labels use an 8x16 font made from the 8x8 font
# (rows doubled, strokes widened by 1 px); each character is a top/bottom tile pair placed in freed glyph tiles.
SHEET = 0x3A000
LABEL_PAIRS = {}
FISHLIST = 0x3D800
# (map, top row, first col, last col, text, align) - the two rows top..top+1, cols first..last are cleared first.
LABELS = [
    (NAME_MAP, 2, 2, 19, 'Enter your name', 'c'),
    (DATE_MAP, 4, 6, 23, 'Enter the date', 'c'),
    (0x3C000, 2, 3, 12, 'Start', 'c'), (0x3C000, 2, 14, 28, 'Erase Data', 'c'),
    (0x3C000, 7, 3, 10, 'Name', 'c'), (0x3C000, 7, 11, 20, 'Fishing', 'c'), (0x3C000, 7, 21, 28, 'Walking', 'c'),
    (0x3D000, 7, 4, 11, 'Angler', 'c'), (0x3D000, 7, 12, 18, 'Size', 'c'), (0x3D000, 7, 19, 29, 'Date', 'c'),
    (0x3D000, 16, 4, 11, 'Angler', 'c'), (0x3D000, 16, 13, 20, 'Got', 'c'), (0x3D000, 16, 21, 29, 'Success', 'c'),
    (0x3C800, 7, 2, 20, 'Are you sure?', 'c'),
    (0x3C800, 6, 23, 29, 'Yes', 'l1'), (0x3C800, 8, 23, 29, 'No', 'l1'),
]
FISH_EN = {'イワナ': 'Char', 'ヤマメ': 'Masu Trout', 'ニジマス': 'Rainbow Trout', 'ヘラブナ': 'W.Crucian',
           'ブラックバス': 'Black Bass', 'ウグイ': 'Dace', 'オイカワ': 'Pale Chub', 'マブナ': 'Crucian Carp',
           'ナマズ': 'Catfish', 'コイ': 'Carp', 'テナガエビ': 'River Prawn', 'ウナギ': 'Eel', 'タナゴ': 'Bitterling',
           'モツゴ': 'Stone Moroko', '川のヌシ': 'River King'}
# Names follow the River King glossary; the right column holds 11 letters, so ヘラブナ is W.Crucian there.
# fish list: rows 3..24 step 3, left names cols 4-17, right names cols 19-29 (16x16 kana at VRAM tile 0x180+code)
KANA16 = {}
for _l in open(os.path.join(HERE, '..', 'data', 'tt_sprite_kana.tbl'), encoding='utf-8'):
    _l = _l.strip()
    if _l and not _l.startswith('#'): KANA16[int(_l[:2], 16)] = _l[3:]
def mapw(r, m, row, col):
    i = col*32 + row; return r[m + 2*i] | r[m + 2*i + 1] << 8
def tile4(rows16):
    """16 rows of 8 colour indices -> two 32-byte 4bpp tiles."""
    out = []
    for half in (rows16[:8], rows16[8:]):
        b = bytearray(32)
        for y, row in enumerate(half):
            for p in range(4):
                v = sum(1 << (7 - x) for x in range(8) if row[x] >> p & 1)
                b[(p // 2)*16 + y*2 + (p & 1)] = v
        out.append(bytes(b))
    return out
DESC = set('gjpqy')
# Descender shapes for the 16 px font (the 8x8 font raises its descenders to keep row 7 clear).
LOW = {'g': ['........', '........', '.#####..', '#....#..', '#....#..', '.#####..', '.....#..', '.####...'],
       'p': ['........', '........', '#####...', '#....#..', '#....#..', '#####...', '#.......', '#.......'],
       'q': ['........', '........', '.#####..', '#....#..', '#....#..', '.#####..', '.....#..', '.....#..'],
       'y': ['........', '........', '#....#..', '#....#..', '#....#..', '.#####..', '.....#..', '.####...'],
       'j': ['....#...', '........', '...##...', '....#...', '....#...', '....#...', '#...#...', '.###....']}
def glyph16(ch):
    from build_font import G
    rows8 = LOW.get(ch) or {c: rows for (code, c), rows in G.items()}[ch]
    img = [[1]*8 for _ in range(16)]
    off = 1
    for y, rr in enumerate(rows8):
        bits = [c == '#' for c in rr]
        bold = [bits[x] or (x and bits[x-1]) for x in range(8)]
        for dy in (0, 1):
            yy = off + 2*y + dy
            if yy < 16:
                for x in range(8):
                    if bold[x]: img[yy][x] = 15
    return img
def patch_labels(r):
    jobs = list(LABELS)
    for k in range(8):
        for side, c0, c1 in (('L', 4, 17), ('R', 19, 29)):
            row = 3 + 3*k
            if row > 24: continue
            codes = [mapw(r, FISHLIST, row, c) & 0x3FF for c in range(c0, c1 + 1, 2)]
            kana = ''.join(KANA16.get(t - 0x180, '') for t in codes if 0x180 <= t < 0x200)
            if kana: jobs.append((FISHLIST, row, c0, c1, FISH_EN[kana], 'l0'))
    jobs.append((FISHLIST, 21, 19, 29, 'River King', 'l0'))
    # clear label boxes
    for m, row, c0, c1, text, al in jobs:
        for rr in (row, row + 1):
            for c in range(c0, c1 + 1): put_map(r, m, rr, c, 0)
    if True:   # the confirm box rows 6-9 hold both answers
        for rr in range(6, 10):
            for c in range(23, 30): put_map(r, 0x3C800, rr, c, 0)
    # which sheet tiles are still referenced?
    used = set()
    for m in (NAME_MAP, DATE_MAP, 0x3C000, 0x3D000, 0x3C800, FISHLIST):
        for i in range(1024):
            t = (r[m + 2*i] | r[m + 2*i + 1] << 8) & 0x3FF
            if t < 0x100: used.add(t)
    cand = [t for t in range(0x100) if t not in used and (t >= 0x60 or (t & 0xF) in range(2, 8) or
            (t & 0xF) in range(9, 14) and 1 <= t >> 4 <= 5 or t in (0x42, 0x43, 0x52, 0x53))]
    cand = [t for t in cand if t not in (0x10, 0x20, 0x30, 0x40, 0x50, 0x51, 0x31, 0x41)]
    chars = sorted(set(''.join(j[4] for j in jobs)) - {' '})
    # pair a top tile with a bottom tile; any two free tiles will do
    assert len(cand) >= 2*len(chars), (len(cand), len(chars))
    pairs = {}
    for i, ch in enumerate(chars):
        top, bot = cand[2*i], cand[2*i + 1]
        t1, t2 = tile4(glyph16(ch))
        r[SHEET + top*32:SHEET + top*32 + 32] = t1; r[SHEET + bot*32:SHEET + bot*32 + 32] = t2
        pairs[ch] = (top, bot)
    LABEL_PAIRS.clear(); LABEL_PAIRS.update(pairs)
    for m, row, c0, c1, text, al in jobs:
        w = c1 - c0 + 1
        start = c0 + (w - len(text)) // 2 if al == 'c' else c0 + int(al[1:])
        assert start >= c0 and start + len(text) - 1 <= c1, (text, c0, c1)
        for j, ch in enumerate(text):
            if ch == ' ': continue
            put_map(r, m, row, start + j, pairs[ch][0]); put_map(r, m, row + 1, start + j, pairs[ch][1])
    # small 8x8 marks: 年 -> '/', 月 -> '/', 日 and 匹 -> blank (fill colour 1)
    from build_font import G
    slash = {c: rows for (code, c), rows in G.items()}['/']
    def small(t, rows):
        img = [[15 if rows and rows[y][x] == '#' else 1 for x in range(8)] for y in range(8)]
        r[SHEET + t*32:SHEET + t*32 + 32] = tile4(img + img)[0]
    small(0x10, slash); small(0x20, slash); small(0x30, None); small(0x40, None)
    return len(chars), len(cand)

# Title screen: はじめる at rows 21-22 cols 12-19 of the title map 0x80800 (tiles 0x2xx of the title set at ROM 0x10000,
# palette 1, colour F with a colour-6 shadow on the right; background word 0x1000). Those 16 tiles are used nowhere
# else on the title, so they are redrawn as "START".
TITLE_MAP, TITLE_TILES = 0x80800, 0x10000
TITLE_FREE = [0x232, 0x233, 0x2E5, 0x206, 0x2E6, 0x2E7, 0x270, 0x271, 0x240, 0x241, 0x2F5, 0x2E8, 0x2F6, 0x2F7, 0x265, 0x275]
def patch_title(r, text='START', col0=None):
    col0 = 12 + (8 - len(text)) // 2 if col0 is None else col0
    for c in range(12, 20):
        for row in (21, 22): put_map(r, TITLE_MAP, row, c, 0x1000)
    free = list(TITLE_FREE)
    for j, ch in enumerate(text):
        img = glyph16(ch)
        img = [[0 if v == 1 else v for v in row] for row in img]          # transparent background
        for y in range(16):                                               # shadow: colour 6 right of each stroke
            for x in range(7, 0, -1):
                if img[y][x] == 0 and img[y][x-1] == 15: img[y][x] = 6
        top, bot = free.pop(0), free.pop(0)
        t1, t2 = tile4(img)
        r[TITLE_TILES + top*32:TITLE_TILES + top*32 + 32] = t1; r[TITLE_TILES + bot*32:TITLE_TILES + bot*32 + 32] = t2
        put_map(r, TITLE_MAP, 21, col0 + j, 0x0600 | top); put_map(r, TITLE_MAP, 22, col0 + j, 0x0600 | bot)

# ---------------------------------------------------------------------------------------------------------------
# Fish name headers. The Japanese headers are 16x16 katakana sprites (sign: list at ROM 0x3E9F4, records: 0x3EBD4,
# 0x20 bytes = 8 sprites each), too few sprites for English names. Instead:
#  * spot signs: the name is drawn on the sign's text layer in 8x16 letters made from spare 8x8 font codes. The
#    sign text routine ($00:BAD9) starts line 1 at the first word of its line table ($00:BB6C); that is moved to
#    row 7 col 0 and line 1 begins with the name (two rows) plus blank padding down to row 14 col 7.
#  * records screen (fish list -> A): the map is loaded with the fish list, before the fish is chosen, so the header
#    routine $00:BC0E gets a JSL to $20:FF00, which writes the name (menu label font) into rows 3-4 of the BG map
#    under a moment of forced blank. Names per fish are 64-byte word lists at $20:F000.
# Both sprite lists are rewritten to park their sprites off screen (y = $F0).
FISH_ORDER = ['Char', 'Masu Trout', 'Rainbow Trout', 'White Crucian', 'Black Bass', 'Dace', 'Pale Chub', 'Crucian Carp',
              'Catfish', 'Carp', 'River Prawn', 'Eel', 'Bitterling', 'Stone Moroko', 'River King']
FREE_CODES = ([c for c in range(0x50, 0x80) if c not in (0x5E, 0x5F, 0x60, 0x61)] +
              [0x9D, 0x9E, 0x9F] + [b + i for b in (0xAC, 0xBC, 0xCC, 0xDC, 0xEC) for i in range(4)] + [0xFC, 0xFD, 0xFE])
MAIN_FONT = 0xAE000
SIGN_LINE_TBL = 0x3B6C          # $00:BB6C, 5 VRAM word addresses
HDR_SIGN, HDR_REC = 0x3E9F4, 0x3EBD4
HOOK = 0x107F00                 # $20:FF00
SIGN_NAME_CODES = {}
def patch_sign_names(r):
    chars = sorted(set(''.join(FISH_ORDER)) - {' '})
    assert 2*len(chars) <= len(FREE_CODES), (len(chars), len(FREE_CODES))
    for i, ch in enumerate(chars):
        top, bot = FREE_CODES[2*i], FREE_CODES[2*i + 1]
        img = [[0 if v == 1 else v for v in row] for row in glyph16(ch)]
        t1, t2 = tile4(img)
        r[MAIN_FONT + top*32:MAIN_FONT + top*32 + 32] = t1; r[MAIN_FONT + bot*32:MAIN_FONT + bot*32 + 32] = t2
        SIGN_NAME_CODES[ch] = (top, bot)
    r[SIGN_LINE_TBL:SIGN_LINE_TBL + 2] = (0x4000 + 7*32).to_bytes(2, 'little')
    for n in range(15):
        o = HDR_SIGN + n*0x20
        r[o:o + 0x20] = bytes([0, 0xF0, 0, 0x32] * 8)
def sign_name_prefix(n):
    """Bytes that draw fish n's name on rows 7-8 and pad to row 14 col 7, where line 1 text starts."""
    name = FISH_ORDER[n]; col0 = (32 - len(name)) // 2
    rows = []
    for half in (0, 1):
        row = [0xFF] * 32
        for j, ch in enumerate(name):
            if ch != ' ': row[col0 + j] = SIGN_NAME_CODES[ch][half]
        rows += row
    return bytes(rows) + b'\xff' * (5*32 + 7)
REC_NAMES = 0x107000              # $20:F000, 16 x 64 bytes: rows 3 and 4, cols 3-18 of the records BG map
REC_VRAM = 0x4000                 # records BG map base (word address, row-major)
def asm_rec_hook():
    """Called from $00:BC0E (records header) after the fish is chosen: forced blank, write the name rows, restore
    full brightness, then redo what the 6 patched bytes did (SEP #$20, LDX #$0040)."""
    c = bytearray()
    c += b'\x08\xc2\x30'                         # PHP; REP #$30
    c += b'\xaf\xd6\x08\x00\x29\x0f\x00'          # LDA $0008D6; AND #$000F
    c += b'\x0a' * 6 + b'\xaa'                     # ASL x6; TAX  -> fish * 64
    c += b'\xe2\x20\xa9\x80\x8f\x00\x21\x00'         # SEP #$20; LDA #$80; STA $002100 (forced blank)
    c += b'\x8f\x15\x21\x00'                     # STA $002115 (increment after high byte)
    c += b'\xc2\x20'                             # REP #$20
    a = 0x8000 | (REC_NAMES & 0x7FFF)
    for row in (3, 4):
        c += b'\xa9' + (REC_VRAM + row*32 + 3).to_bytes(2, 'little') + b'\x8f\x16\x21\x00'   # LDA #addr; STA $002116
        c += b'\xa0\x10\x00'                     # LDY #$0010
        loop = len(c)
        c += b'\xbf' + a.to_bytes(2, 'little') + b'\x20'     # LDA $20:F000,X
        c += b'\x8f\x18\x21\x00\xe8\xe8\x88'           # STA $002118; INX; INX; DEY
        c += b'\xd0' + bytes([(loop - (len(c) + 2)) & 0xFF])
    c += b'\xe2\x20\xa9\x0f\x8f\x00\x21\x00'           # SEP #$20; LDA #$0F; STA $002100 (full brightness)
    c += b'\x28\xe2\x20\xa2\x40\x00\x6b'             # PLP; SEP #$20; LDX #$0040; RTL
    return bytes(c)
def patch_records(r):
    for n in range(16):
        words = [0] * 32
        if 1 <= n <= 15:
            for j, ch in enumerate(FISH_ORDER[n - 1]):
                if ch != ' ': words[j], words[16 + j] = LABEL_PAIRS[ch]
        r[REC_NAMES + n*64:REC_NAMES + (n + 1)*64] = b''.join(w.to_bytes(2, 'little') for w in words)
    code = asm_rec_hook()
    r[HOOK:HOOK + len(code)] = code
    a = 0x8000 | (HOOK & 0x7FFF)
    assert r[0x3C0E:0x3C14] == bytes.fromhex('08e220a24000'), r[0x3C0E:0x3C14].hex()
    r[0x3C0E:0x3C14] = bytes([0x08, 0x22, a & 0xFF, a >> 8, 0x20, 0xEA])     # PHP; JSL $20:FF00; NOP
    for n in range(15):
        o = HDR_REC + n*0x20
        r[o:o + 0x20] = bytes([0, 0xF0, 0, 0x32] * 8)

# ---------------------------------------------------------------------------------------------------------------
# Bad-save message: a list of 58 8x8 sprites at ROM 0x3E90C (x, y, tile, attr 0x31). Sprite tile = font code + 0x80
# on OBJ page 1, i.e. the main 8x8 font, so English is one sprite per character.
BACKUP_LIST, BACKUP_SLOTS = 0x3E90C, 58
BACKUP_LINES = [(0x50, 'Backup data is damaged!'), (0x68, 'Press the START button.'), (0x78, 'A new game will begin.')]
def patch_backup_msg(r):
    recs = []
    for y, text in BACKUP_LINES:
        x0 = (256 - 8*len(text)) // 2
        for j, ch in enumerate(text):
            if ch != ' ': recs.append(bytes([x0 + 8*j, y, (ENC[ch] + 0x80) & 0xFF, 0x31]))
    assert len(recs) <= BACKUP_SLOTS, len(recs)
    recs += [bytes([0, 0xF0, 0, 0x31])] * (BACKUP_SLOTS - len(recs))
    r[BACKUP_LIST:BACKUP_LIST + 4*BACKUP_SLOTS] = b''.join(recs)

# HUD labels in the sprite sheet at ROM 0x36800: つりの力 = tiles 28-2B, 歩く力 = 2C-2E, each with a second row
# (tiles +0x10) for the outline. Colour F text with a colour 9 outline, drawn from the 8x8 font, packed tightly.
HUD_SHEET = 0x36800
HUD_LABELS = [(0x28, 4, 'Fish'), (0x2C, 3, 'Walk')]
def glyph_cols(ch):
    from build_font import G
    rows = {c: rr for (code, c), rr in G.items()}[ch]
    cols = [x for x in range(8) if any(rr[x] == '#' for rr in rows)]
    return rows, cols[0], cols[-1]
def patch_hud(r):
    for base, n, text in HUD_LABELS:
        W = 8*n
        img = [[0]*W for _ in range(16)]
        x = 1; pieces = []
        for ch in text:
            rows, a, b = glyph_cols(ch); pieces.append((x - a, rows)); x += b - a + 2
        shift = (W - (x - 1)) // 2
        for ox, rows in pieces:
            for y, rr in enumerate(rows):
                for xx, cch in enumerate(rr):
                    if cch == '#' and 0 <= ox + xx + shift < W: img[1 + y][ox + xx + shift] = 15
        for y in range(16):
            for xx in range(W):
                if img[y][xx] == 0 and any(0 <= y + dy < 16 and 0 <= xx + dx < W and img[y + dy][xx + dx] == 15
                                           for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                    img[y][xx] = 9
        for k in range(n):
            t1, t2 = tile4([row[8*k:8*k + 8] for row in img])
            r[HUD_SHEET + (base + k)*32:HUD_SHEET + (base + k + 1)*32] = t1
            r[HUD_SHEET + (base + 0x10 + k)*32:HUD_SHEET + (base + 0x11 + k)*32] = t2
