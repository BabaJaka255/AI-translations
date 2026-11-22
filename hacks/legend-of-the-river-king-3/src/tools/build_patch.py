"""Build the English ROM: python3 build_patch.py ORIGINAL.gba OUT.gba

Scripts are re-stored uncompressed in the expanded ROM area. A hook on the script loader's call to the
game's decompressor copies blocks whose header byte is 0x00 (the game's own blocks use 0x70).
"""
import json, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from k5lib import Rom
from script import parse
from textcodec import encode

ROOT = os.path.dirname(HERE)
HOOK_AT = 0x083F6000          # free space at the end of the original 4 MB
DATA_AT = 0x08400000          # expanded area (ROM grows to 8 MB)
SCRIPT_LOAD_BL = 0x0803EC04   # bl decompress  in the script loader
RELOC = {0x0a: 20, 0x0b: 20, 0x0c: 20, 0x0d: 20, 0x0e: 20, 0x0f: 20, 0x12: 4, 0x13: 4}
TEXT_OPS = (0x16, 0x1b)
NAME_HOOK_AT = HOOK_AT + 0x100
NAME_CALL_BL = 0x08012BB6     # bl 0x0800D810 (identity) in text code 03 = player name
DEFAULT_NAME_PTR = 0x0800D800 # literal pointing at the default name 渓太
DEFAULT_NAME_AT = HOOK_AT + 0x200
DEFAULT_NAME = 'ＫＥＩＴＡ'

# Name-entry side labels 英数 記号 戻る 進む 終了. The game finds them by comparing the first cell's character
# (in a signed binary search at 0x0800688C), so the first characters must not be typeable on any page:
# lowercase full-width letters, ★ and ≪ ≫ are not. The search is replaced by a plain compare chain.
NAME_LABELS = {0xFB72C: 'ａｂ', 0xFB744: '★♪', 0xFB75C: '≪　', 0xFB774: '≫　', 0xFB78C: 'ｏｋ'}
NAME_KEY_AT = 0x0800688C      # replaced by a jump to NAME_KEY_HOOK (the literals after it stay intact)
NAME_KEY_HOOK = HOOK_AT + 0x300
def sj(c): return struct.unpack('>H', c.encode('cp932'))[0]
NAME_KEY_JUMP = f'''
  ldr r0, [pc, #0]
  bx r0
  .word {NAME_KEY_HOOK | 1:#x}
'''
NAME_KEY = f'''
  ldr r0, =0x8140
  cmp r1, r0
  beq k_space
  ldr r0, ={sj('ａ')}
  cmp r1, r0
  beq k_eisu
  ldr r0, ={sj('★')}
  cmp r1, r0
  beq k_kigou
  ldr r0, ={sj('≫')}
  cmp r1, r0
  beq k_susumu
  ldr r0, ={sj('≪')}
  cmp r1, r0
  beq k_modoru
  ldr r0, ={sj('ｏ')}
  cmp r1, r0
  beq k_owari
  ldr r0, =0x08006A05
  bx r0
k_space:
  ldr r0, =0x080069CF
  bx r0
k_eisu:
  ldr r0, =0x08006909
  bx r0
k_kigou:
  ldr r0, =0x08006919
  bx r0
k_susumu:
  ldr r0, =0x08006955
  bx r0
k_modoru:
  ldr r0, =0x08006945
  bx r0
k_owari:
  ldr r0, =0x0800696D
  bx r0
'''

# Raw (uncompressed) blocks for any caller of the decompressor: the first 8 bytes of 0x08040D20 jump to
# DECOMP_HOOK, which copies blocks whose header byte is 0x00 and otherwise replays the overwritten
# instructions and continues at 0x08040D28.
DECOMP_AT = 0x08040D20
DECOMP_HOOK = HOOK_AT + 0x400
DECOMP_JUMP = f'''
  ldr r2, [pc, #0]
  bx r2
  .word {DECOMP_HOOK | 1:#x}
'''
DECOMP = '''
  ldrb r2, [r0]
  cmp r2, #0
  beq raw
  push {r4, r5, r6, r7, lr}
  mov r4, r8
  mov r5, sb
  mov r6, sl
  ldr r2, =0x08040D29
  bx r2
raw:
  ldr r2, [r0]
  lsrs r2, r2, #8
  adds r2, #3
  lsrs r2, r2, #2
  adds r0, #4
loop:
  ldm r0!, {r3}
  stm r1!, {r3}
  subs r2, #1
  bne loop
  bx lr
'''
TITLE_OBJ_REFS = (0x56C4, 0x3DD5C)    # -> 0x08365D40, title sprite tiles (32 KB, compressed)
TITLE_BANK_REFS = (0x56DC, 0x3DD74)   # -> 0x08368D18, title sprite frames
TITLE_PAL = 0x369098                  # title OBJ palette (raw)
TITLE_FRAME_TAB = 0x15153C            # u16 offsets of the 8 frames in the bank
TITLE_ANIM_TAB = 0x15154C             # u16 offsets of the 8 records after them

# Dialogue font: 10 rows of u16 per glyph, bit 8 = leftmost pixel of the 6-px cell. There is no glyph for 'O'
# (it shares '0'), so glyphs from 'P' on sit one slot lower. m and M were 4 px wide; logo.WIDE has 5-px ones.
FONT = 0x32F538
def glyph_at(ch): c = ord(ch); return FONT + 20 * (c - 1 if c > 0x4F else c)
import logo as _logo
import tags
GLYPHS = _logo.WIDE

ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
def asm(src, addr):
    b, _ = ks.asm(src, addr); return bytes(b)

def bl(frm, to):
    o = (to - (frm + 4)) >> 1
    return struct.pack('<HH', 0xF000 | ((o >> 11) & 0x7FF), 0xF800 | (o & 0x7FF))

HOOK = '''
  ldrb r2, [r0]
  cmp r2, #0
  beq raw
  ldr r2, =0x08040D21
  bx r2
raw:
  ldr r2, [r0]
  lsrs r2, r2, #8
  adds r2, #3
  lsrs r2, r2, #2
  adds r0, #4
loop:
  ldm r0!, {r3}
  stm r1!, {r3}
  subs r2, #1
  bne loop
  bx lr
'''

# Player name for text code 03: full-width A-Z/0-9 -> ASCII (Capitalised), full-width spaces dropped,
# kana/kanji left alone. Result goes to a small buffer at the top of EWRAM.
NAME_HOOK = '''
  push {r4, r5, lr}
  ldr r1, =0x0203FFC0
  mov r5, r1
  movs r4, #0
next:
  ldrb r2, [r0]
  cmp r2, #0
  beq done
  cmp r2, #0x80
  blo ascii
  ldrb r3, [r0, #1]
  adds r0, #2
  cmp r2, #0x81
  bne not81
  cmp r3, #0x40
  beq next
not81:
  cmp r2, #0x82
  bne copy2
  mov r2, r3
  subs r2, #0x4f
  cmp r2, #9
  bls digit
  mov r2, r3
  subs r2, #0x60
  cmp r2, #25
  bls upper
  mov r2, r3
  subs r2, #0x81
  cmp r2, #25
  bls lower
  movs r2, #0x82
copy2:
  strb r2, [r1]
  strb r3, [r1, #1]
  adds r1, #2
  movs r4, #1
  b next
digit:
  adds r2, #0x30
  b put
upper:
  cmp r4, #0
  bne lower
  adds r2, #0x41
  b put
lower:
  adds r2, #0x61
  b put
ascii:
  adds r0, #1
put:
  strb r2, [r1]
  adds r1, #1
  movs r4, #1
  b next
done:
  strb r2, [r1]
  mov r0, r5
  pop {r4, r5, pc}
'''

def rebuild(data, texts):
    """texts: {old_offset: new_text_bytes}. Returns new script bytes with jumps relocated."""
    size, ins = parse(data)
    out = bytearray(); newpos = {}; fix = []
    for off, op, raw, t in ins:
        newpos[off] = len(out)
        if op in TEXT_OPS:
            tb = texts.get(off, t.rstrip(b'\0')) if t is not None else b''
            tb = tb + b'\0'
            tb += b'\0' * ((-len(tb)) % 4)
            out += raw[:4] + struct.pack('<I', len(tb)) + tb
        else:
            if op in RELOC: fix.append((len(out) + RELOC[op], off))
            out += raw
    newpos[len(data)] = len(out)
    body = bytearray(b'[SCRIPT]' + struct.pack('<I', 0) + out)
    # positions above are relative to body start at 12
    for at, _ in fix:
        old = struct.unpack_from('<I', body, at + 12)[0]
        struct.pack_into('<I', body, at + 12, newpos[old + 12])
    struct.pack_into('<I', body, 8, len(body) - 12)
    return bytes(body)

def load_translations():
    path = os.path.join(ROOT, 'out', 'script.json')
    tr = {}
    for e in json.load(open(path)):
        if not e.get('en'): continue
        for w in e['where']:
            s, off, op = w.split(':')
            tr.setdefault(int(s), {})[int(off, 16)] = e['en']
    return tr

def find_refs(d, addr):
    t = struct.pack('<I', 0x08000000 + addr)
    return [j for j in range(0, len(d), 4) if d[j:j + 4] == t]

def load_ui(d):
    """text/ui_en.txt: 'index<TAB>English' lines indexing out/ui_jp.json, or '@hexaddr<TAB>English' for a
    string not in the dump (its pointers are found by scanning). Returns [(refs, text)]."""
    ui = json.load(open(os.path.join(ROOT, 'out', 'ui_jp.json')))
    out = []
    for line in open(os.path.join(ROOT, 'text', 'ui_en.txt'), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'): continue
        i, t = line.split('\t', 1)
        if i.startswith('@'): out.append((find_refs(d, int(i[1:], 16)), t))
        else: out.append(([int(r, 16) for r in ui[int(i)]['refs']], t))
    return out

def place(rom, pos, blob, refs):
    o = pos - 0x08000000
    rom[o:o + len(blob)] = blob
    for r in refs: struct.pack_into('<I', rom, r, pos)
    return pos + len(blob) + ((-len(blob)) % 4)

def build(src, dst, extra=None):
    r = Rom(src)
    rom = bytearray(r.d) + b'\xff' * (0x800000 - len(r.d))
    hook = asm(HOOK, HOOK_AT)
    rom[HOOK_AT - 0x08000000: HOOK_AT - 0x08000000 + len(hook)] = hook
    rom[SCRIPT_LOAD_BL - 0x08000000: SCRIPT_LOAD_BL - 0x08000000 + 4] = bl(SCRIPT_LOAD_BL, HOOK_AT)
    nh = asm(NAME_HOOK, NAME_HOOK_AT)
    assert len(nh) < 0x100
    rom[NAME_HOOK_AT - 0x08000000: NAME_HOOK_AT - 0x08000000 + len(nh)] = nh
    rom[NAME_CALL_BL - 0x08000000: NAME_CALL_BL - 0x08000000 + 4] = bl(NAME_CALL_BL, NAME_HOOK_AT)
    dn = DEFAULT_NAME.encode('shift_jis') + b'\0'
    rom[DEFAULT_NAME_AT - 0x08000000: DEFAULT_NAME_AT - 0x08000000 + len(dn)] = dn
    struct.pack_into('<I', rom, DEFAULT_NAME_PTR - 0x08000000, DEFAULT_NAME_AT)
    dh = asm(DECOMP, DECOMP_HOOK); assert len(dh) < 0x100
    rom[DECOMP_HOOK - 0x08000000: DECOMP_HOOK - 0x08000000 + len(dh)] = dh
    rom[DECOMP_AT - 0x08000000: DECOMP_AT - 0x08000000 + 8] = asm(DECOMP_JUMP, DECOMP_AT)
    tr = load_translations()
    if extra:
        for k, v in extra.items(): tr.setdefault(k, {}).update(v)
    table = r.script_table(); ptrs = r.script_ptrs()
    pos = DATA_AT
    from charmap import CHARMAP
    for i in sorted(tr):
        orig = r.decompress(ptrs[i])
        texts = {off: encode(s, CHARMAP) for off, s in tr[i].items()}
        body = rebuild(orig, texts)
        blob = struct.pack('<I', (len(body) << 8) | 0x00) + body
        blob += b'\0' * ((-len(blob)) % 4)
        o = pos - 0x08000000
        rom[o:o + len(blob)] = blob
        struct.pack_into('<I', rom, table + 4 * i - 0x08000000, pos)
        pos += len(blob)
    # UI strings: write new copies after the scripts and repoint every reference
    for refs, t in load_ui(r.d):
        b = encode(t, CHARMAP) + b'\0'
        b += b'\0' * ((-len(b)) % 4)
        o = pos - 0x08000000
        rom[o:o + len(b)] = b
        for r in refs: struct.pack_into('<I', rom, r, pos)
        pos += len(b)
    # title logo (tools/logo.py): raw sprite tiles, rebuilt frames A/B/C + the rest of the bank, palette 32-127
    import logo
    r = Rom(src)
    blk, bank, lpal = logo.make(r.d, r.decompress(0x08365D40))
    pos = place(rom, pos, struct.pack('<I', len(blk) << 8) + blk, TITLE_OBJ_REFS)
    pos = place(rom, pos, bank + r.d[logo.BANK_REST:TITLE_PAL], TITLE_BANK_REFS)
    # the bank is addressed through u16 offset tables: 8 frames, then 8 animation records
    delta = len(bank) - (logo.BANK_REST - logo.BANK)
    nb = struct.unpack_from('<H', bank, 0)[0]
    struct.pack_into('<HH', rom, TITLE_FRAME_TAB + 2, 4 + 8 * nb, 4 + 8 * nb + 12)
    for k in range(3, 8):
        struct.pack_into('<H', rom, TITLE_FRAME_TAB + 2 * k, struct.unpack_from('<H', r.d, TITLE_FRAME_TAB + 2 * k)[0] + delta)
    for k in range(8):
        struct.pack_into('<H', rom, TITLE_ANIM_TAB + 2 * k, struct.unpack_from('<H', r.d, TITLE_ANIM_TAB + 2 * k)[0] + delta)
    rom[TITLE_PAL + 2 * logo.PAL_LO: TITLE_PAL + 2 * logo.PAL_LO + len(lpal)] = lpal
    # Fishing Note area maps (tools/maplabels.py): English place-name scrolls, tiles and tilemaps stored raw
    import maplabels
    for i, (tiles, tmap, _) in maplabels.build(r).items():
        for tab, blob in ((maplabels.TILES, tiles), (maplabels.MAPS, tmap)):
            refs = [tab + 4 * k for k in ((0, 1) if i == 0 else (i + 1,))]
            pos = place(rom, pos, struct.pack('<I', len(blob) << 8) + blob, refs)
    # name-entry side labels (u16 little-endian Shift-JIS cells, two per label)
    nk = asm(NAME_KEY, NAME_KEY_HOOK)
    assert len(nk) < 0x100
    rom[NAME_KEY_HOOK - 0x08000000: NAME_KEY_HOOK - 0x08000000 + len(nk)] = nk
    nj = asm(NAME_KEY_JUMP, NAME_KEY_AT)
    assert len(nj) == 8
    rom[NAME_KEY_AT - 0x08000000: NAME_KEY_AT - 0x08000000 + 8] = nj
    for at, txt in NAME_LABELS.items():
        cells = b''.join(c.encode('cp932')[::-1] for c in txt)
        rom[at:at + len(cells)] = cells
    for ch, rows in GLYPHS.items():
        for y, row in enumerate(rows):
            struct.pack_into('<H', rom, glyph_at(ch) + 2 * y, sum(1 << (8 + x) for x, c in enumerate(row) if c == '#'))
    tags.patch_equip_tag(rom)
    # fix header checksum
    chk = (-(sum(rom[0xA0:0xBD]) + 0x19)) & 0xFF
    rom[0xBD] = chk
    open(dst, 'wb').write(rom)
    return pos

if __name__ == '__main__':
    print(hex(build(sys.argv[1], sys.argv[2])))
