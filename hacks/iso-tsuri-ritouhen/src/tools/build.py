"""Build the English patch for Iso Tsuri: Ritou-hen (SFC).

python3 tools/build.py            -> build/iso_en.sfc + build/iso_en.bps

Layout of the expanded 32 Mbit ROM:
  $E0:0000-FFFF  copy of bank $C1 (the text bank). The text reader is pointed here, so every old 16-bit text
                 pointer still works and English strings can be written over the copy (non-text bytes in
                 this copy are never read).
  $E1:1000       8x16 ASCII font (16 bytes per glyph, top 8 rows then bottom 8 rows)
  $E1:2000       glyph -> old 8x8 index table (row 0 / HUD use)
  $E1:2100       old 8x8 index -> ASCII glyph table (digits etc. drawn by code)
  $E1:2200       records-by-fish menu slot -> fish id (written by script_en)
  $E1:3000       code
  $E1:4000       title screen BG3 tiles (LZ), $E1:6000 its map (LZ, 6-byte header kept)
  $E1:8000       bold proportional story font (data/font_story.txt), advances at $E1:9000
"""
import os, sys, zlib, hashlib, glob
HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
# romhack toolkit (rhtk, writes the BPS): $RHTK, else src/toolkit (published copy), else the workspace one
for _tk in (os.environ.get('RHTK'), os.path.join(GAME, 'toolkit'), os.path.join(GAME, '..', '..', 'romhack-toolkit')):
    if _tk and os.path.isdir(os.path.join(_tk, 'rhtk')):
        sys.path.insert(0, _tk); break
import asm65
from rhtk.patch import bps_create

ROM_SHA1 = '49741c14e923bdaa0ff5776744508544921cbb2d'

def hirom(addr):
    """$BB:AAAA -> file offset"""
    return ((addr >> 16) & 0x3f) << 16 | (addr & 0xffff) if (addr >> 16) < 0xC0 else (addr - 0xC00000)

class Rom:
    def __init__(self, data):
        self.d = bytearray(data)
    def expect(self, off, hexbytes):
        b = bytes.fromhex(hexbytes)
        if self.d[off:off + len(b)] != b:
            raise SystemExit('unexpected bytes at %06X: %s (wanted %s)' % (off, self.d[off:off + len(b)].hex(), hexbytes))
    def put(self, off, b):
        self.d[off:off + len(b)] = b
    def patch(self, off, old, new):
        self.expect(off, old); self.put(off, bytes.fromhex(new) if isinstance(new, str) else new)

def load_rom():
    cands = glob.glob(os.path.join(GAME, 'rom', '*.sfc'))
    for c in cands:
        d = open(c, 'rb').read()
        if hashlib.sha1(d).hexdigest() == ROM_SHA1: return d
    raise SystemExit('original ROM (SHA-1 %s) not found in rom/' % ROM_SHA1)

# ---------------------------------------------------------------- font
def load_story_font(path=None):
    """data/font_story.txt -> (rows {code: 16 ints, bit 15 = leftmost pixel}, advances {code: px})."""
    path = path or os.path.join(GAME, 'data', 'font_story.txt')
    L = open(path, encoding='utf-8').read().split('\n')
    rows, adv = {}, {}
    for i, ln in enumerate(L):
        if ln[:2] and all(c in '0123456789ABCDEF' for c in ln[:2]) and ' w=' in ln:
            code = int(ln[:2], 16)
            adv[code] = int(ln.rsplit('w=', 1)[1])
            rows[code] = [int(r.replace('#', '1').replace('.', '0').ljust(16, '0'), 2) for r in L[i + 1:i + 17]]
            assert all(r & 0x7F == 0 for r in rows[code]), 'story glyphs are at most 9 px wide'
    return rows, adv

def story_width(text):
    _, adv = load_story_font()
    return sum(adv[ord(c)] for c in text)

def build_font():
    from PIL import PcfFontFile
    pcf = PcfFontFile.PcfFontFile(open(os.path.join(HERE, 'fonts', 'koi8x16.pcf'), 'rb'))
    out = bytearray(0x1000)
    for code in range(0x20, 0x7f):
        g = pcf.glyph[code]
        if g is None: continue
        im = g[3]
        w, h = im.size
        assert (w, h) == (8, 16)
        px = im.load()
        rows = [sum(0x80 >> x for x in range(8) if px[x, y]) for y in range(16)]
        b = bytes(rows[:8] + rows[8:])
        out[code * 16:code * 16 + 16] = b
        out[(code | 0x80) * 16:(code | 0x80) * 16 + 16] = b
    return bytes(out)

# old 8x8 index of a few ASCII chars (table at $81:945F order)
OLD_INDEX = {' ': 0, ':': 13, '.': 28, 'k': 29, 'g': 30, '?': 31, 'c': 11, 'm': 12}
for i in range(10): OLD_INDEX[str(i)] = 1 + i

def tables():
    asc2old = bytearray(256)       # glyph&FF -> old index (0 = blank)
    for ch, idx in OLD_INDEX.items():
        asc2old[ord(ch)] = idx; asc2old[ord(ch) | 0x80] = idx
    old2asc = bytearray(256)       # old index -> ascii (0 = keep old glyph)
    for ch, idx in OLD_INDEX.items():
        if ch in ' :.0123456789':
            old2asc[idx] = ord(ch); old2asc[idx | 0x80] = ord(ch)
    return bytes(asc2old), bytes(old2asc)

FONT = 0xE11000
ASC2OLD = 0xE12000
OLD2ASC = 0xE12100
CODE = 0xE13000
SFONT = 0xE18000     # bold proportional story font: 128 glyphs x 16 rows x 16 bits
SADV = 0xE19000      # its advances (1 byte per code)

HOOKS = r'''
; ---- character lookup, called from $80:9229 (A = byte, 8-bit; X 16-bit). Returns X = glyph, $03 = $8000.
lookup:
  .a8
  .i16
  PHA
  LDX #$8000
  STX $03
  PLA
  CMP #$20
  BCC search
  CMP #$7F
  BCS search
  REP #$20
  AND #$00FF
  ORA #$0100
  TAX
  SEP #$20
  RTL
search:
  LDX #$FFFF
s1:
  INX
  CPX #$0100
  BEQ nf
  CMP $945F,X
  BNE s1
  RTL
nf:
  LDX #$0000
  RTL

; ---- half-width glyph draw, replaces $80:9346 (A16 = glyph|$8000[|$4000], X = buffer offset)
hwdraw:
  .a16
  PHA
  PHX
  AND #$01FF
  CMP #$0100
  BCS asc
  TAX
  SEP #$20
  LDA OLD2ASC.l,X
  REP #$20
  AND #$00FF
  BNE asc
  JMP old
asc:
  AND #$00FF
  TAX
  LDA $054B
  BNE big
  ; row 0 (HUD): draw the matching old 8x8 glyph
  SEP #$20
  LDA ASC2OLD.l,X
  REP #$20
  AND #$00FF
  ORA #$8000
  PLX
  JSR draw8
  PLA
  INC $0549
  RTL
big:
  TXA
  ASL A
  ASL A
  ASL A
  ASL A
  TAY
  PLX
  PHB
  SEP #$20
  LDA #$E1
  PHA
  PLB
  LDA #$08
  STA $00
bl:
  LDA FONT,Y
  AND $01
  STA $7F4600,X
  LDA FONT,Y
  AND $02
  STA $7F4601,X
  LDA FONT+8,Y
  AND $01
  STA $7F4800,X
  LDA FONT+8,Y
  AND $02
  STA $7F4801,X
  INY
  INX
  INX
  DEC $00
  BNE bl
  REP #$20
  PLB
  PLA
  INC $0549
  RTL
old:
  PLX
  PLA
  PHA
  PHX
  JSR draw8
  PLX
  PLA
  AND #$4000
  BEQ od
  TXA
  CLC
  ADC #$FE00
  TAX
  LDA $04A3
  JSR draw8
od:
  INC $0549
  RTL

; copy of $80:9362: draw old 8x8 glyph A (index|flags) at X, font pointer [$81:84C0]
draw8:
  ASL A
  ASL A
  ASL A
  CLC
  ADC $84C0
  TAY
  PHB
  SEP #$20
  LDA $84C2
  PHA
  PLB
  LDA #$08
  STA $00
d8:
  LDA $0000,Y
  AND $01
  STA $7F4800,X
  LDA $0000,Y
  AND $02
  STA $7F4801,X
  INY
  INX
  INX
  DEC $00
  BNE d8
  REP #$20
  PLB
  RTS
; ---- records-by-fish menu: A = menu slot -> fish id (replaces the row/column arithmetic at $80:89E0)
fishmap:
  .a16
  TAX
  LDA FISHMAP.l,X
  AND #$00FF
  RTL

; ---- record list: X = index * 32 (replaces 4x ASL at $80:8B60)
asl5:
  .a16
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  RTL

; ---- story crawl character, replaces $80:E109 (JML from bank $80, A16 = glyph). Full-width glyphs go back to
; the original code; half-width (bit 15) are drawn proportionally from the bold story font (SFONT: 16 rows x
; 16 bits per glyph, bit 15 = leftmost; advances at SADV) at pixel column P ($7E:1D00, free RAM).
; Line buffer $7F:4800 + line*$400: 8 px tile column t is at ((t & 15) << 4) + ((t >> 4) << 9), its bottom
; half $100 further, 2bpp with plane 1 left 0. $08E1 still counts characters; it is 2 at the start of a line.
; Scratch: $00 row, $02 shift, $04 shifted bits, $06 old P, $08/$0A tile offsets, $0C row offset (saved).
storych:
  .a16
  PHX
  PHY
  PHA
  BIT #$8000
  BNE sthalf
  JML $80E10C
sthalf:
  AND #$00FF
  CMP #$00A0
  BNE sth1
  LDA #$0020
sth1:
  AND #$007F
  TAX
  PHB
  PEI ($00)
  PEI ($02)
  PEI ($04)
  PEI ($06)
  PEI ($08)
  PEI ($0A)
  PEI ($0C)
  LDA $08E3
  XBA
  ASL A
  ASL A
  STA $0C
  LDA $08E1
  CMP #$0002
  BNE stcont
  LDA #$0010
  STA $7E1D00
  PHX
  LDX $0C
  LDY #$0200
stclr:
  LDA #$0000
  STA $7F4800,X
  INX
  INX
  DEY
  BNE stclr
  PLX
stcont:
  LDA SADV.l,X
  AND #$00FF
  STA $04
  LDA $7E1D00
  STA $06
  CLC
  ADC $04
  CMP #$00F1
  BCC stfit
  JMP stdone
stfit:
  STA $7E1D00
  LDA $06
  AND #$0007
  STA $02
  LDA $06
  LSR A
  LSR A
  LSR A
  PHA
  JSR sttoff
  STA $08
  PLA
  INC A
  JSR sttoff
  STA $0A
  TXA
  ASL A
  ASL A
  ASL A
  ASL A
  ASL A
  TAX
  SEP #$20
  LDA #$7F
  PHA
  PLB
  REP #$20
  STZ $00
strow:
  LDA SFONT.l,X
  BEQ stnext
  LDY $02
  BEQ stns
stsh:
  LSR A
  DEY
  BNE stsh
stns:
  STA $04
  LDA $00
  AND #$0007
  ASL A
  STA $0C
  LDA $00
  AND #$0008
  BEQ strw
  LDA #$0100
  CLC
  ADC $0C
  STA $0C
strw:
  LDA $08
  CLC
  ADC $0C
  TAY
  SEP #$20
  LDA $05
  ORA $4800,Y
  STA $4800,Y
  REP #$20
  LDA $0A
  CLC
  ADC $0C
  TAY
  SEP #$20
  LDA $04
  ORA $4800,Y
  STA $4800,Y
  REP #$20
stnext:
  INX
  INX
  INC $00
  LDA $00
  CMP #$0010
  BNE strow
stdone:
  PLA
  STA $0C
  PLA
  STA $0A
  PLA
  STA $08
  PLA
  STA $06
  PLA
  STA $04
  PLA
  STA $02
  PLA
  STA $00
  PLB
  INC $08E1
  PLA
  JML $80E14A
; tile column A (0-31) -> offset of its top half in the current line ($08E3 line, via $0C = line * $400)
sttoff:
  PHA
  AND #$000F
  ASL A
  ASL A
  ASL A
  ASL A
  STA $04
  PLA
  AND #$0010
  BEQ stt1
  LDA #$0200
stt1:
  CLC
  ADC $04
  CLC
  ADC $0C
  RTS
'''

def build(script=None, out_name='iso_en'):
    rom = Rom(load_rom())
    orig = bytes(rom.d)
    rom.d += b'\xff' * 0x200000
    rom.patch(0xFFD7, '0b', '0c')                       # ROM size 32 Mbit
    # text bank copy and reader bank
    rom.put(hirom(0xE00000), orig[0x10000:0x20000])
    rom.patch(0x9281, 'a9c1', 'a9e0')
    # font + tables
    rom.put(hirom(FONT), build_font())
    rows, adv = load_story_font()
    sf = bytearray(0x1000); sa = bytearray(0x80)
    for c, rs in rows.items():
        for y, r in enumerate([0] + rs[:15]):      # 1 row lower: sits better in the text box
            sf[c * 32 + y * 2:c * 32 + y * 2 + 2] = r.to_bytes(2, 'little')
        sa[c] = adv[c]
    rom.put(hirom(SFONT), bytes(sf)); rom.put(hirom(SADV), bytes(sa))
    a2o, o2a = tables()
    rom.put(hirom(ASC2OLD), a2o); rom.put(hirom(OLD2ASC), o2a)
    # icon glyphs A-M in the old half-width table move to codes 01-0D
    for i, pos in enumerate([44, 45, 46, 47, 59, 60, 61, 62, 63, 76, 77, 78, 79]):
        off = 0x1945F + pos
        rom.expect(off, '%02x' % (0x41 + i))
        rom.d[off] = 1 + i
    code, labels = asm65.assemble(HOOKS, CODE, {'FONT': FONT & 0xffff, 'OLD2ASC': OLD2ASC, 'ASC2OLD': ASC2OLD, 'FISHMAP': 0xE12200,
                                                   'SFONT': SFONT, 'SADV': SADV})
    rom.put(hirom(CODE), code)
    L = lambda n: labels[n]
    jsl = lambda a: bytes([0x22, a & 0xff, (a >> 8) & 0xff, a >> 16])
    rom.patch(0x9229, 'a200808603205f92', jsl(L('lookup')) + b'\xea' * 4)
    rom.patch(0x9346, '48da206293', jsl(L('hwdraw')) + b'\x60')
    rom.patch(0xE109, 'da5a4820', bytes([0x5C]) + L('storych').to_bytes(3, 'little'))
    rom.patch(0xDF70, '07', '02')                      # story: frames per character (English has ~2.5x more)
    rom.patch(0xDF7B, '02', '01')                      # ... while A is held
    rom.labels = labels
    if script: script(rom, orig)
    import title_logo; title_logo.insert(rom.d)
    fix_checksum(rom.d)
    os.makedirs(os.path.join(GAME, 'build'), exist_ok=True)
    out = bytes(rom.d)
    open(os.path.join(GAME, 'build', out_name + '.sfc'), 'wb').write(out)
    open(os.path.join(GAME, 'build', out_name + '.bps'), 'wb').write(bps_create(orig, out))
    print('built %s.sfc  CRC32 %08X  code %d bytes' % (out_name, zlib.crc32(out), len(code)))
    return out, labels

def fix_checksum(d):
    d[0xFFDC:0xFFE0] = b'\xff\xff\x00\x00'
    s = sum(d) & 0xffff
    d[0xFFDE] = s & 0xff; d[0xFFDF] = s >> 8
    c = s ^ 0xffff
    d[0xFFDC] = c & 0xff; d[0xFFDD] = c >> 8

if __name__ == '__main__':
    import script_en
    build(script_en.apply)
