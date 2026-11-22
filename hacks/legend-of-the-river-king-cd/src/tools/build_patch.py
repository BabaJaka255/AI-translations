"""Build the English data track.  usage: build_patch.py track02.bin out_track02.bin
Patches are applied to both data copies (copy 2 = sector + 1478)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from asm6280 import asm
from cdsector import mode1
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PREGAP = 224; COPY2 = 1478; RAW = 2352
FONT_SECTOR = 38           # zero run 38-57 (and 1516-1535)
FONT_BANK = 0x68           # Super CD-ROM RAM: needs System Card 3.0
MAIN_SECTOR = 58           # main program, loaded to $A000 (banks $86/$87)

class Track:
    def __init__(s, path):
        s.raw = bytearray(open(path, 'rb').read()); s.dirty = set()
    def read(s, sec, off=0, n=2048):
        p = (PREGAP + sec) * RAW + 16 + off; return bytes(s.raw[p:p + n])
    def write(s, sec, off, data, both=True):
        for base in ((0, COPY2) if both else (0,)):
            o = off; d = data; n = sec + base
            while d:
                n += o // 2048; o %= 2048; k = min(len(d), 2048 - o)
                p = (PREGAP + n) * RAW + 16 + o; s.raw[p:p + k] = d[:k]; s.dirty.add(PREGAP + n)
                d = d[k:]; o += k
    def write_main(s, addr, data, expect=None):
        off = addr - 0xA000
        if expect is not None:
            cur = s.read(MAIN_SECTOR + off // 2048, off % 2048, len(expect))
            assert cur == expect, 'unexpected bytes at $%04X: %s' % (addr, cur.hex())
        s.write(MAIN_SECTOR, off, data)
    def save(s, path):
        for n in s.dirty: s.raw[n * RAW:(n + 1) * RAW] = mode1(s.raw[n * RAW:(n + 1) * RAW])
        open(path, 'wb').write(s.raw)

BOOT = '''
    lda $fff5
    clc
    adc #$06
    tam #$20
    inc
    tam #$40
    lda #$00
    sta $fc
    lda #$00
    sta $fd
    lda #$3a
    sta $fe
    lda #$01
    sta $ff
    lda #$00
    sta $fa
    lda #$a0
    sta $fb
    lda #$08
    sta $f8
    jsr read
    jsr loadfont
    jmp $a000
read:                     ; CD_READ with retry from the second copy (original code)
    ldx #7
r1: lda $f8,x
    sta $00,x
    dex
    bpl r1
    jsr $e009
    beq r3
    ldx #7
r2: lda $00,x
    sta $f8,x
    dex
    bpl r2
    clc
    lda $fe
    adc #$c6
    sta $fe
    lda $fd
    adc #$05
    sta $fd
    jsr $e009
r3: rts
loadfont:                 ; English font -> bank FONT_BANK (Super CD-ROM RAM)
    tma #$08
    pha
    stz $fc
    stz $fd
    lda #FONT_SECTOR
    sta $fe
    lda #$03
    sta $ff
    lda #FONT_BANK
    sta $fa
    lda #$01
    sta $f8
    jsr read
    pla
    tam #$08
    rts
'''

# New glyph code at $BCA7: a looped tile writer (replaces 788 bytes of unrolled code) and the English glyph hook.
GLYPH = '''
tiles:                    ; 16x16 1bpp glyph at $C12E -> 4 tiles at VRAM [$18]
    clx
t0: lda #$00
    sta $f7
    sta !$0000
    lda $18
    sta !$0002
    lda $19
    sta !$0003
    lda #$02
    sta $f7
    sta !$0000
    phx
    ldy #$08
t1: lda $c12e,x
    sta !$0002
    sta !$0003
    inx
    inx
    dey
    bne t1
    plx
    phx
    ldy #$08
t2: lda #$ff
    sta !$0002
    lda $c12e,x
    sta !$0003
    inx
    inx
    dey
    bne t2
    clc
    lda #$10
    adc $18
    sta $18
    bcc t3
    inc $19
t3: pla
    eor #$01
    tax
    and #$01
    bne t0
    txa
    clc
    adc #$10
    tax
    cpx #$20
    bne t0
    rts

glyph:                    ; $F8/$F9 = the two bytes of a text word
    lda $f9
    bmi kanji
    php
    sei
    tma #$04
    pha
    lda #FONT_BANK
    tam #$04
    lda $f8
    clx
    jsr half
    lda $f9
    ldx #$01
    jsr half
    pla
    tam #$04
    plp
    rts
kanji:
    lda #$2e
    sta $fa
    lda #$c1
    sta $fb
    stz $ff
    jmp $e060
half:                     ; A = ASCII, X = 0 left / 1 right
    sec
    sbc #$20
    stz $fb
    asl
    rol $fb
    asl
    rol $fb
    asl
    rol $fb
    asl
    rol $fb
    sta $fa
    lda $fb
    ora #$40
    sta $fb
    cly
h1: lda ($fa),y
    sta $c12e,x
    inx
    inx
    iny
    cpy #$10
    bne h1
    rts

menufont:                 ; menu letters: font -> VRAM $7000 as 8x16 (tile pairs), 192 tiles
    php
    sei
    tma #$04
    pha
    lda #FONT_BANK
    tam #$04
    lda #$00
    sta $f7
    sta !$0000
    lda #$00
    sta !$0002
    lda #$70
    sta !$0003
    lda #$02
    sta $f7
    sta !$0000
    stz $fa
    lda #$40
    sta $fb
    ldx #192
m0: cly
m1: lda ($fa),y
    sta !$0002
    sta !$0003
    iny
    cpy #$08
    bne m1
    cly
m2: lda #$ff
    sta !$0002
    lda ($fa),y
    sta !$0003
    iny
    cpy #$08
    bne m2
    clc
    lda $fa
    adc #$08
    sta $fa
    bcc m3
    inc $fb
m3: dex
    bne m0
    pla
    tam #$04
    plp
    rts
'''
SYMS = dict(FONT_SECTOR=FONT_SECTOR, FONT_BANK=FONT_BANK)

def enc(text):
    """English text -> game string (ASCII byte pairs, 0000 end)."""
    b = text.encode('ascii')
    if len(b) % 2: b += b' '
    return b + b'\0\0'

def insert_script(t):
    """Write every translated string over its Japanese slot (in place, both copies)."""
    import json
    from encode import encode
    from tr_main import DIALOGUE, FIXED
    items = json.load(open(os.path.join(ROOT, 'out', 'script.json')))
    n = 0
    for it in items:
        en = DIALOGUE.get(it['jp'])
        if en is None: continue
        b = encode(en, reflow=not en.startswith(' '))   # keep leading spaces (" landed!", centred lines)
        assert len(b) <= it['size'], (it['id'], en)
        t.write(0, it['off'], b + bytes(it['size'] - len(b))); n += 1
    for off, (size, en) in FIXED.items():
        b = encode(en, reflow=False); assert len(b) <= size, (hex(off), en)
        t.write(0, off, b + bytes(size - len(b))); n += 1
    from tr_main import ANIMALS
    offs = bytearray(); names = bytearray()
    for a in ANIMALS:
        offs.append(len(names)); s = (' ' + a) if len(a) % 2 else a
        names += s.encode('ascii') + b'\0\0'
    assert len(ANIMALS) == 25 and len(names) <= 0xF2, len(names)
    t.write(0, 0x1F886, bytes(offs)); t.write(0, 0x1F89F, bytes(names) + bytes(0xF2 - len(names)))
    return n

MENU_SECTORS = (9, 19, 20, 21, 27, 28, 29, 65, 66)
def is_blank(w): return (w & 0xFFF) in (0x28F, 0x272)
def insert_menus(t):
    """Rewrite window templates: kanji glyph cells -> 8x16 letters (tiles $700 + 2*(c-32) and +1)."""
    from templates import find_labels
    from tr_menus import LABELS
    data = bytearray()
    for n in range(1478): data += t.read(n)
    done = 0
    for p, b, n, jp in find_labels(bytes(data), 0, 1478 * 2048):
        if p // 2048 not in MENU_SECTORS: continue
        en = LABELS[jp]
        room = n
        while True:
            q1, q2 = p + 2 * room, b + 2 * room
            wt = data[q1] | data[q1 + 1] << 8; wb = data[q2] | data[q2 + 1] << 8
            if is_blank(wt) and is_blank(wb) and room < n + 4: room += 1
            else: break
        assert len(en) <= room, (jp, en, room)
        en = en.ljust(n)
        for k, ch in enumerate(en):
            for base, half in ((p, 0), (b, 1)):
                o = base + 2 * k; w = data[o] | data[o + 1] << 8
                pal = (w & 0xF000) if not is_blank(w) or True else 0x7000
                tile = 0x700 + 2 * (ord(ch) - 32) + half
                nw = pal | tile
                data[o] = nw & 255; data[o + 1] = nw >> 8
                t.write(0, o, bytes([nw & 255, nw >> 8]))
        done += 1
    return done

def build(src, dst, strings=None):
    t = Track(src)
    boot = asm(BOOT, 0x4000, SYMS); assert len(boot) < 2048
    for sec in (2,):
        t.write(sec, 0, boot + bytes(2048 - len(boot)))
    font = open(os.path.join(ROOT, 'data', 'font_en.bin'), 'rb').read()
    t.write(FONT_SECTOR, 0, font + bytes(2048 - len(font)))
    code = asm(GLYPH, 0xBCA7, SYMS); syms = asm.syms
    assert 0xBCA7 + len(code) <= 0xBFBC, hex(len(code))
    t.write_main(0xBCA7, code + bytes(0xBFBC - 0xBCA7 - len(code)), expect=bytes.fromhex('a90085f78d0000'))
    stub = asm('jsr %d\n bra $bbf3' % syms['glyph'], 0xBBE4)
    t.write_main(0xBBE4, stub + b'\xea' * (15 - len(stub)), expect=bytes.fromhex('a92e85faa9c185fba90085ff2060e0'))
    for addr, (limit, text) in (strings or {}).items():
        e = enc(text); assert len(e) <= limit, (hex(addr), len(e), limit)
        t.write_main(addr, e)
    n = insert_script(t)
    print('menu labels', insert_menus(t))
    t.write(34, 0x37D, asm('jsr %d\n jmp $83c9' % syms['menufont'], 0x837D))
    import signs
    print('sign tiles', signs.patch(t, b''.join(t.read(n) for n in range(1478))))
    import catch_names
    print('catch names', catch_names.rebuild(t))
    import fish_guide
    print('fish guide pool', fish_guide.rebuild(t))
    import logo
    print('logo sprites', logo.patch(t))
    import title_sprites
    for off, data, exp in title_sprites.patches():
        sec, o = divmod(off, 2048)
        if exp is not None: assert t.read(sec, o, len(exp)) == exp, hex(off)
        t.write(sec, o, data)
    t.save(dst)
    print('inserted', n, 'strings')
    return len(code), 0xBFBC - 0xBCA7

if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2]))
