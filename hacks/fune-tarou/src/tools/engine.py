"""Engine patches for the English build (see notes/rom.md, "English engine").

1. ROM grows from 16 to 32 Mbit. The new half starts as a byte copy of the old half, so any stray
   mirror access still reads the same data.
2. Strings are read from bank E1 instead of C1 (one byte in the reader at $C0:79F0). E1 starts as a
   copy of C1, so untouched strings keep their addresses; English strings are rewritten there.
3. Single-byte characters map straight to glyph = byte (no table search, $C0:79CE).
4. Single-byte glyphs become 8x16: the renderer's dakuten branch ($C0:7B8A) now always draws a top
   tile, glyph 256+code, one row above. Font: 512 8x8 1bpp glyphs at $F0:1000: tall font at codes $00-$7F,
   compact font at $80-$FF (picked with '>' through $08BD, like the old hiragana half).
5. The opening speech draws letters proportionally from its own font ($F0:2000).
"""
from ftlib import *
import lz, asm

CODE = 0x300000          # $F0:0000 our code
FONT = 0x301000          # $F0:1000 our 8x8 font (512 glyphs, 4 KB)
OLD_FONT8 = 0x108D0B     # $D0:8D0B original 8x8 font (256 glyphs)
OLD_TABLE = 0x1939B      # $C1:939B original single-byte -> glyph table (96 used)
LOW = 0x80               # compact font: glyph = code + $80 (bottom tile), 256 + code + $80 (top tile)
HOOK_CODE = 0x5C         # fishhook icon (old glyph of byte $74)


def put(rom, off, data, expect=None):
    if expect is not None:
        assert rom[off:off + len(expect)] == expect, 'unexpected bytes at %06X: %s' % (off, rom[off:off + len(expect)].hex())
    rom[off:off + len(data)] = data


def build_font(rom, glyphs, low):
    """Tall font (data/font_en.txt) at codes $00-$7F, compact font (data/font_low.txt) at $80-$FF.
    The compact half replaces the old half-width kana, which English text never uses."""
    font = bytearray(512 * 8)
    for base, gl in ((0, glyphs), (LOW, low)):
        for code, rows in gl.items():
            g = base + code
            font[(256 + g) * 8:(256 + g) * 8 + 8] = bytes(rows[:8])
            font[g * 8:g * 8 + 8] = bytes(rows[8:])
    font[HOOK_CODE * 8:HOOK_CODE * 8 + 8] = rom[OLD_FONT8 + rom[OLD_TABLE:OLD_TABLE + 96].index(0x74) * 8:][:8]
    font[(256 + HOOK_CODE) * 8:(256 + HOOK_CODE) * 8 + 8] = bytes(8)
    return font


def catch_list_tilemap(orig):
    src = 0x0D3F36
    data, n = lz.decompress(orig, src + 6)
    w = [data[i] | data[i + 1] << 8 for i in range(0, len(data), 2)]
    # the resource is 64x32 words; the game splits it into a 32x64 map: screen row k < 32 is data row
    # 2k, screen row 32 + k is data row 2k + 1
    for r in range(7, 60):                      # screen rows of the list boxes (row 7 joins the title box)
        d = 2 * r if r < 32 else 2 * (r - 32) + 1
        row = w[d * 32:(d + 1) * 32]
        if r != 7:
            row[1] = row[4]; row[30] = row[27]  # outer borders move out to cols 1 and 30
        row[2] = row[3] = row[4] = row[5]       # fill
        row[27] = row[28] = row[29] = row[17]
        w[d * 32:(d + 1) * 32] = row
    packed = lz.compress(b''.join(bytes([x & 255, x >> 8]) for x in w))
    return bytes(orig[src:src + 7]) + packed[1:]  # keep the header and the stream's first byte


SPEECH = 0x302000        # $F0:2000 speech font: 128 glyphs x 16 rows x 16 bits; advances at $F0:3000


def load_speech_font(path=None):
    """data/font_speech.txt -> (rows {code: 16 ints, bit 15 = leftmost pixel}, advances {code: px})."""
    path = path or os.path.join(GAME, 'data', 'font_speech.txt')
    L = open(path, encoding='utf-8').read().split('\n')
    rows, adv = {}, {}
    for i, ln in enumerate(L):
        if ln[:2] and all(c in '0123456789ABCDEF' for c in ln[:2]) and ' w=' in ln:
            code = int(ln[:2], 16)
            adv[code] = int(ln.rsplit('w=', 1)[1])
            rows[code] = [int(r.replace('#', '1').replace('.', '0').ljust(16, '0'), 2) for r in L[i + 1:i + 17]]
            assert all(r & 0x7F == 0 for r in rows[code]), 'speech glyphs are at most 9 px wide'
    return rows, adv


def speech_font_data():
    rows, adv = load_speech_font()
    data = bytearray(0x1080)
    for code, rs in rows.items():
        for y, r in enumerate(rs):
            data[code * 32 + y * 2:code * 32 + y * 2 + 2] = r.to_bytes(2, 'little')
        data[0x1000 + code] = adv[code]
    return bytes(data)


SPEECH_WIDTH = 224        # px per line: 16 px margins on a 256 px screen


def speech_width(text):
    """Pixel width of a line in the speech font."""
    from ftlib import encode_en
    _, adv = load_speech_font()
    return sum(adv[b] for b in encode_en(text))


def dialog_code():
    # Single-byte characters are drawn proportionally at pixel column P ($7F:F008) of the line bitmap
    # ($7F:5000, cleared by $C0:C5DE at the start of each line, which also sets $0C61 = 2; lines start at P = 16, 16 px in from the screen edge). Tile column t
    # of the line: top tile at ((t >> 4) << 9) + ((t & 15) << 4), bottom tile $100 further; plane 0 only.
    # Scratch at $7F:F020-$7F:F031 (untouched RAM): code, P & 7, tile offsets, row, shifted bits, row offset.
    items = [
        'da 5a 8b',                       # PHX / PHY / PHB
        '89 00 80', ('bra', 0xD0, 'single'),
        '48', ('jsr', 'alloc'), 'aa', '68',      # wide: X = cell, Y = glyph * 32 + $B000
        '0a 0a 0a 0a 0a 18 69 00 b0 a8',
        '8b e2 20 a9 7e 48 ab a9 10 85 00',
        ('label', 'wl'),
        'b9 00 00 9f 00 50 7f a9 00 9f 01 50 7f',
        'b9 10 00 9f 00 51 7f a9 00 9f 01 51 7f',
        'c8 e8 e8 c6 00', ('bra', 0xD0, 'wl'),
        'c2 20 ab', ('jmp', 'done'),
        ('label', 'single'),
        '29 7f 00 8f 20 f0 7f',                         # code
        'ad 61 0c c9 02 00', ('bra', 0xD0, 'cont'),     # $0C61 = 2: a new line
        'a9 10 00 8f 08 f0 7f',                         # P = 16
        ('label', 'cont'),
        'af 20 f0 7f 0a 0a 0a 0a 0a a8',                # Y = code * 32
        'af 08 f0 7f 29 07 00 8f 22 f0 7f',             # s = P & 7
        'af 08 f0 7f 4a 4a 4a 48', ('jsr', 'ta'), '8f 26 f0 7f',   # tile offsets of t = P >> 3 and t + 1
        '68 1a', ('jsr', 'ta'), '8f 28 f0 7f',
        'a9 00 00 8f 2a f0 7f',                         # row = 0
        'e2 20 a9 f0 48 ab c2 20',                      # DB = $F0
        ('label', 'row'),
        'b9 00 20', ('bra', 0xF0, 'next'),              # LDA $2000,Y (glyph row) / BEQ next
        '48 af 22 f0 7f aa 68',
        ('label', 'sh'), 'e0 00 00', ('bra', 0xF0, 'shd'), '4a ca', ('bra', 0x80, 'sh'),
        ('label', 'shd'), '8f 2c f0 7f',
        'af 2a f0 7f 29 07 00 0a 8f 2e f0 7f',          # row offset = (row & 7) * 2 + (row & 8) * 32
        'af 2a f0 7f 29 08 00 0a 0a 0a 0a 0a 18 6f 2e f0 7f 8f 2e f0 7f',
        '18 6f 26 f0 7f aa',
        'e2 20 af 2d f0 7f 1f 00 50 7f 9f 00 50 7f c2 20',     # left byte into tile t
        'af 2e f0 7f 18 6f 28 f0 7f aa',
        'e2 20 af 2c f0 7f 1f 00 50 7f 9f 00 50 7f c2 20',     # right byte into tile t + 1
        ('label', 'next'),
        'c8 c8 af 2a f0 7f 1a 8f 2a f0 7f c9 10 00', ('bra', 0xD0, 'row'),
        'af 20 f0 7f aa bd 00 30 29 ff 00 18 6f 08 f0 7f 8f 08 f0 7f',   # P += advance
        'a9 03 00 8f 61 0c 7e',                         # $0C61 = 3: not a new line any more
        ('label', 'done'),
        'ab 7a fa ad 5b 0c 6b',           # PLB / PLY / PLX / LDA $0C5B / RTL
        # ta: A = tile column -> offset of its top tile in the line bitmap
        ('label', 'ta'),
        '48 29 0f 00 0a 0a 0a 0a 8f 30 f0 7f 68 29 f0 00 0a 0a 0a 0a 0a 18 6f 30 f0 7f 60',
        # alloc: same as $C0:C6E3 (cell offset of ($0C61, $0C63), then step the cursor)
        ('label', 'alloc'),
        'ad 63 0c eb 0a 0a 8d 3c 13',
        'ad 61 0c 29 07 00 0a 0a 0a 0a 0a 18 6d 3c 13 8d 3c 13',
        'ad 61 0c 29 08 00', ('bra', 0xF0, 'a1'),
        'a9 00 02 18 6d 3c 13 8d 3c 13',
        ('label', 'a1'),
        'ee 61 0c ad 61 0c c9 10 00', ('bra', 0x90, 'a2'),
        '9c 61 0c ee 63 0c ad 63 0c c9 10 00', ('bra', 0x90, 'a2'),
        '9c 63 0c',
        ('label', 'a2'),
        'ad 3c 13 60',
        # wait: X = frames to wait after a character (A = character)
        ('label', 'wait'),
        'a2 0c 00 89 00 80', ('bra', 0xF0, 'w1'), 'a2 04 00',
        ('label', 'w1'),
        '6b',
    ]
    return asm.assemble(items, 0xF00100)


TITLE_SUB_PNG = os.path.join(GAME, 'gfx', 'edit', 'title-subtitle.png')   # hand-drawn, see make_title_subtitle.py
TITLE_SUB_RIGHT, TITLE_SUB_TOP = 250, 78   # right edge and top of the lettering, in screen pixels
TITLE_OBJ_TILE = 480       # first of the OBJ tiles 480-511 (free on the title screen)
TITLE_OAM = 120            # OAM entries 120-127 (the title uses 0-107)
TITLE_OBJ_PAL = 7          # OBJ palette 7 (CGRAM 240-255, black on the title)


def snes_color(rgb):
    r, g, b = rgb[:3]
    return (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10


def title_subtitle_parts():
    """-> (VRAM records, OAM entries for 8 sprites, palette of 16 words)."""
    from PIL import Image
    im = Image.open(TITLE_SUB_PNG).convert('RGBA')
    w, h = im.size
    assert h <= 16 and w <= 128, 'the subtitle must fit eight 16x16 sprites'
    colors = []
    px = {}
    for y in range(h):
        for x in range(w):
            c = im.getpixel((x, y))
            if c[3] < 128:
                continue
            k = snes_color(c)
            if k not in colors:
                colors.append(k)
            px[(x, y)] = colors.index(k) + 1
    assert len(colors) <= 15, 'the subtitle may use 15 colors'
    pal = [0] + colors + [0] * (15 - len(colors))
    def tile(tx, ty):
        b = bytearray(32)
        for y in range(8):
            for x in range(8):
                c = px.get((tx * 8 + x, ty * 8 + y), 0)
                for bit in range(4):
                    if c >> bit & 1:
                        b[(bit >> 1) * 16 + y * 2 + (bit & 1)] |= 0x80 >> x
        return b
    top = bytearray(); bot = bytearray()
    for tx in range(16):
        top += tile(tx, 0); bot += tile(tx, 1)
    def rec(addr, data):
        return addr.to_bytes(2, 'little') + (len(data) // 2).to_bytes(2, 'little') + bytes(data)
    base = 0x7000 + (TITLE_OBJ_TILE - 256) * 16        # second OBJ name table (OBSEL base $6000)
    vram = rec(base, top) + rec(base + 0x100, bot) + bytes(2)
    n = (w + 15) // 16
    x0 = TITLE_SUB_RIGHT - w
    oam = bytearray()
    for k in range(8):
        if k < n:
            oam += bytes([(x0 + 16 * k) & 0xFF, TITLE_SUB_TOP - 1, (TITLE_OBJ_TILE + 2 * k) & 0xFF,
                          0x30 | TITLE_OBJ_PAL << 1 | 1])        # priority 3, palette, second name table
        else:
            oam += bytes([0, 0xE0, 0, 0])
    return vram, bytes(oam), b''.join(v.to_bytes(2, 'little') for v in pal)


def title_code(vram_addr, oam_addr, pal_addr):
    """Two hooks. $C0:C1E2 LDA #0 / STA $1282 (title fade-in start, forced blank) -> JSL $F03100: subtitle tiles
    to VRAM, its palette into the CGRAM buffer ($15D1, uploaded when $17D3 is set), flag $7F:F040 = 1.
    $C0:69A6 LDA #1 / STA $1276 (every frame, after the sprite builders, before the OAM upload) -> JSL $F03180:
    flag 1 puts the subtitle in OAM entries 120-127 of the buffer at $1349; flag 2 (set by the next screen
    setup) hides them once and clears the flag."""
    L = lambda a: a.to_bytes(3, 'little').hex()
    oam_buf = 0x7E1349 + TITLE_OAM * 4
    hi = 0x7E1349 + 0x200 + TITLE_OAM // 4
    pal_buf = 0x7E15D1 + (128 + TITLE_OBJ_PAL * 16) * 2
    a = asm.assemble([
        '08 c2 30 e2 20 a9 80 8d 15 21 c2 20 a2 00 00',
        ('label', 'rec'),
        'bf' + L(vram_addr), ('bra', 0xF0, 'end'),
        '8d 16 21 e8 e8 bf' + L(vram_addr) + 'a8 e8 e8',
        ('label', 'w'),
        'bf' + L(vram_addr) + '8d 18 21 e8 e8 88', ('bra', 0xD0, 'w'), ('bra', 0x80, 'rec'),
        ('label', 'end'),
        'a2 00 00',
        ('label', 'pl'),
        'bf' + L(pal_addr) + '9f' + L(pal_buf) + 'e8 e8 e0 20 00', ('bra', 0xD0, 'pl'),
        'a9 01 00 8d d3 17',                            # palette upload request
        'e2 20 a9 01 8f 40 f0 7f c2 20',                # flag = 1
        'a9 00 00 8d 82 12 28 6b',                      # replaced: LDA #0 / STA $1282; PLP / RTL
    ], 0xF03100)[0]
    b = asm.assemble([
        '08 c2 30 af 40 f0 7f 29 ff 00',
        'c9 01 00', ('bra', 0xF0, 'show'),
        'c9 02 00', ('bra', 0xD0, 'done'),
        'a9 00 00 8f 40 f0 7f a2 00 00',               # hide once
        ('label', 'hl'),
        'a9 00 e0 9f' + L(oam_buf) + 'a9 00 00 9f' + L(oam_buf + 2) + 'e8 e8 e8 e8 e0 20 00', ('bra', 0xD0, 'hl'),
        ('bra', 0x80, 'done'),
        ('label', 'show'),
        'a2 00 00',
        ('label', 'sl'),
        'bf' + L(oam_addr) + '9f' + L(oam_buf) + 'e8 e8 e0 20 00', ('bra', 0xD0, 'sl'),
        'e2 20 a9 aa 8f' + L(hi) + '8f' + L(hi + 1) + 'c2 20',   # 16x16, X < 256
        ('label', 'done'),
        '28 a9 01 00 8d 76 12 6b',                      # PLP; replaced: LDA #1 / STA $1276; RTL
    ], 0xF03180)[0]
    return a, b

def apply(orig):
    rom = bytearray(orig) + bytearray(orig)          # 4 MB, upper half mirrors the lower half
    rom[0xFFD7] = 0x0C                                 # ROM size: 32 Mbit
    # 2. string bank C1 -> E1:  $C0:79F0  LDA #$C1
    put(rom, 0x79F0, bytes([0xA9, TEXT_BANK_NEW]), expect=bytes([0xA9, 0xC1]))
    # the label bubble routine $C0:7F54 measures its text in bank C1 too:  $C0:7F5D  LDA #$C1
    put(rom, 0x7F5D, bytes([0xA9, TEXT_BANK_NEW]), expect=bytes([0xA9, 0xC1]))
    # '>' still sets $08BD = $80 (the hiragana half of the old font), which now picks the compact font;
    # '<' (and the start of every string, $C0:791A) sets it back to 0
    # 3. single-byte lookup:  $C0:79CE  REP #$20 / AND #$00FF / TAX / SEP #$20 / RTS
    put(rom, 0x79CE, bytes.fromhex('c22029ff00aae22060'), expect=bytes.fromhex('a2ffffe8e00001f006'))
    # 4. top tile for every single-byte glyph: $C0:7B8A  LDA $00 / AND #$4000 / BEQ +$3C
    #    -> JSL $F00040 / NOP x3, which turns $08BB into (code & $FF) | $100 for the existing branch
    #    The glyph routine $C0:7BCE clobbers the low byte of $00, so the code is saved on entry to
    #    the draw routine ($C0:7AA4 STA $00 / LDA $08B9 -> JSL $F00000 / NOP) in $08BB.
    #    A single-byte space draws no tiles: it blanks its two tilemap cells, steps one column and
    #    leaves through the end of the draw routine ($C0:7B47 PLY / PLX / RTS). English has many more
    #    spaces than the Japanese, and the text tiles would otherwise run into other graphics.
    put(rom, 0x7AA4, bytes([0x22, 0x00, 0x00, 0xF0, 0xEA]), expect=bytes.fromhex('8500adb908'))
    hook1 = bytes.fromhex(
        '8500'        # STA $00
        '297fc0'      # AND #$C07F   (either font)
        'c92080'      # CMP #$8020   (single-byte space)
        'f009'        # BEQ space
        'a500'        # LDA $00
        '8dbb08'      # STA $08BB
        'adb908'      # LDA $08B9
        '6b'          # RTL
        # space:
        'ad6309' '0a0a0a0a0a' '18' '6d6109' '0a' 'aa'   # X = ((row << 5) + col) << 1
        'a90000' '9f00407f' '9fc03f7f'                  # blank this cell and the one above
        'ee6109'                                        # INC $0961
        'e220' '686868' 'c220'                          # drop the JSL return address
        '5c477bc0')                                     # JML $C0:7B47 (PLY / PLX / RTS)
    assert len(hook1) <= 0x40
    put(rom, CODE, hook1)
    put(rom, 0x7B8A, bytes([0x22, 0x40, 0x00, 0xF0, 0xEA, 0xEA, 0xEA]), expect=bytes.fromhex('a500290040f03c'))
    put(rom, CODE + 0x40, bytes.fromhex('adbb08' '29ff00' '090001' '8dbb08' '6b'))
    # The glyph routine $C0:7BCE takes the font address from the resource table ($8132/$8134 through
    # DB=$01). Sprite text loads the same table entry, so the table stays and the routine gets
    # immediates instead:  ADC $8132 -> ADC #$1000,  LDA $8134 -> LDA #$F0 / NOP
    put(rom, 0x7BD2, bytes([0x69, FONT & 0xFF, (FONT >> 8) & 0xFF]), expect=bytes.fromhex('6d3281'))
    put(rom, 0x7BD9, bytes([0xA9, 0xF0, 0xEA]), expect=bytes.fromhex('ad3481'))
    # The HUD number font ($C0:7A38: fuel, sizes, scores) indexes 2bpp tiles at $C1:93FB by the
    # position of the character in the old table, so that path converts the byte back:
    # $C0:7A3C  ASL x4 -> JSL $F00060  (A = table index * 16)
    put(rom, 0x7A3C, bytes([0x22, 0x60, 0x00, 0xF0]), expect=bytes.fromhex('0a0a0a0a'))
    put(rom, CODE + 0x60, bytes.fromhex(
        'da'          # PHX
        'e220'        # SEP #$20
        '297f'        # AND #$7F     (either font)
        'a20000'      # LDX #$0000
        'df9b93c1'    # loop: CMP $C1939B,X
        'f009'        # BEQ found
        'e8'          # INX
        'e06000'      # CPX #$0060
        'd0f4'        # BNE loop
        'a21f00'      # LDX #$001F   ('?')
        # found:
        'c220'        # REP #$20
        '8a'          # TXA
        '0a0a0a0a'    # ASL x4
        'fa'          # PLX
        '6b'))        # RTL
    # The fishhook icon in front of the top-right HUD counter is byte $74 ('t') drawn through the text
    # path ($C0:808D LDA #$74). English needs 't', so the icon moves to code $5C (no ASCII use here).
    put(rom, 0x808E, bytes([HOOK_CODE]), expect=bytes([0x74]))
    # (the records screen draws angler names and numbers with $08BD = $80: the compact font, as wanted)
    # Catch list (Y on the map): the two name boxes widen from 10 to 13 columns each (cols 1-14 and
    # 17-30, flush with the title box). The box tilemap is an LZ resource ($C1:8760 -> $CD:3F36:
    # 6-byte header + stream); a stretched copy goes to $F0:0800 and the pointer follows it.
    tm = catch_list_tilemap(orig)
    assert len(tm) <= 0x800
    put(rom, CODE + 0x800, tm)
    put(rom, 0x18760, bytes([0x00, 0x08, 0xF0]), expect=bytes.fromhex('363fcd'))
    # Opening speech window ($C1:C5DE loop, glyphs drawn by $C0:C730 into a 16x16-cell bitmap at
    # $7F:5000). Single-byte characters are drawn proportionally from the speech font
    # (data/font_speech.txt, $F0:2000); wide ones are drawn as before. $C0:C615 JSR $C730 / LDA $0C5B ->
    # JSL $F00100 / NOP x2, and the per-character delay ($C0:C61F) becomes 4 frames for letters instead of 12.
    code, labels = dialog_code()
    assert len(code) <= 0x700, len(code)   # $F0:0100-$F0:07FF
    put(rom, CODE + 0x100, code)
    put(rom, 0xC615, bytes([0x22, 0x00, 0x01, 0xF0, 0xEA, 0xEA]), expect=bytes.fromhex('2030c7ad5b0c'))
    w = 0xF00100 + labels['wait']
    put(rom, 0xC61F, bytes([0x68, 0x22, w & 0xFF, (w >> 8) & 0xFF, w >> 16, 0xEA, 0xEA, 0xEA, 0xEA]),
        expect=bytes.fromhex('a20c0068d003a20600'))
    # '>' (compact font) stays in force after its string ends, so the name field and the angler names that are
    # drawn later use it too. Lists (labels, fish names) drawn on later screens must not inherit it: every
    # screen setup ($C0:D89F) and the catch list exits ($C0:6F7A, $C0:7087) reset $08BD along with BG3's scroll.
    # STZ $2112 / STZ $2112 -> JSL $F000C0 / NOP NOP
    for site in (0xD89F, 0x6F7A, 0x7087):
        put(rom, site, bytes([0x22, 0xC0, 0x00, 0xF0, 0xEA, 0xEA]), expect=bytes.fromhex('9c12219c1221'))
    # ... and the title subtitle flag ($7F:F040, see title_code) goes from 1 to 2 (hide once)
    put(rom, CODE + 0xC0, bytes.fromhex('9c1221' '9c1221' '9cbd08'     # STZ $2112 x2 / STZ $08BD
        '08' 'e220' '48' 'af40f07f' 'c901' 'd006' 'a902' '8f40f07f'      # PHP / SEP / PHA / flag 1 -> 2
        '68' '28' '6b'))                                               # PLA / PLP / RTL
    put(rom, SPEECH, speech_font_data())
    # English subtitle under the title logo: hand-drawn sprites (gfx/edit/title-subtitle.png)
    vram, oam, pal = title_subtitle_parts()
    a, b = title_code(0xF03200, 0xF03700, 0xF03720)
    assert len(a) <= 0x80 and len(b) <= 0x80 and len(vram) <= 0x500
    put(rom, CODE + 0x3100, a)
    put(rom, CODE + 0x3180, b)
    put(rom, CODE + 0x3200, vram)
    put(rom, CODE + 0x3700, oam)
    put(rom, CODE + 0x3720, pal)
    put(rom, 0x69A6, bytes([0x22, 0x80, 0x31, 0xF0, 0xEA, 0xEA]), expect=bytes.fromhex('a901008d7612'))
    put(rom, 0xC1E2, bytes([0x22, 0x00, 0x31, 0xF0, 0xEA, 0xEA]), expect=bytes.fromhex('a900008d8212'))
    put(rom, FONT, build_font(orig, load_font(), load_font(os.path.join(GAME, 'data', 'font_low.txt'))))
    return rom
