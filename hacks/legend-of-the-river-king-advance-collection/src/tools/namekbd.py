# Name entry keyboards (both games). The keyboard is a 256-tile LZ77 block, two LZ77 tilemaps (hiragana and
# katakana pages), two 85-byte layout tables (cursor position -> tile) and a conversion table tile -> text codes.
# The name buffer holds tile numbers, so English only needs new glyph art, layouts and maps.
import struct
import font_en, encode_en
from lzscan import lz77
from gfx import lz77_compress

KBD = {
    'g4': dict(block=0xe6018, maps=[0xe68f8, 0xe6a90], mapptrs=[0x1fe620, 0x1fe624, 0x1fe628],
               table=0x1fe62c, tptrs=[0x1fe72c, 0x1fe730, 0x1fe734], conv=0x1fb490, convlen=0x200, free=[]),
    # game 3 has no tiles for 0-9 / A-Z; the katakana tiles 4B-7C are reused (one page only now)
    'g3': dict(block=0x1be95c, maps=[0x1bf18c, 0x1bf324], mapptrs=[0x20127c, 0x201280],
               table=0x201284, tptrs=[0x201330, 0x201334], conv=0x200530, convlen=0x140, free=list(range(0x4b, 0x7d))),
}
BLANK = 0x96
LAYOUT = [
    'ABCDE' 'abcde' '01234',
    'FGHIJ' 'fghij' '56789',
    'KLMNO' 'klmno' '.,!?-',
    'PQRST' 'pqrst' "'&~♥ ",
    'UVWXY' 'uvwxy' '     ',
    'Z    ' 'z    ',
]
PROMPT = 'Enter your name.'

def code_of(ch, game):
    if ch == '♥': return 0xb0
    return encode_en.CODES[ch]

def tile_for(ch, conv, game):
    c = code_of(ch, game)
    for i in range(len(conv) // 2):
        if conv[2 * i] == c and conv[2 * i + 1] == 0xff: return i
    raise KeyError((ch, game))

def heart_tile():
    rows = ['', ' # # ', '#####', '#####', ' ### ', '  #  ']
    b = bytearray()
    for y in range(8):
        r = rows[y] if y < len(rows) else ''
        px = [3 if x < len(r) and r[x] == '#' else 1 for x in range(8)]
        for x in range(0, 8, 2): b.append(px[x] | px[x + 1] << 4)
    return bytes(b)

def patch_map(m, old_rows, new_rows, prompt_old, prompt_new):
    hw = list(struct.unpack('<%dH' % (len(m) // 2), m))
    def find(seq):
        n = len(seq)
        for i in range(len(hw) - n + 1):
            if all((hw[i + k] & 0x3ff) == seq[k] for k in range(n)): return i
        return -1
    for old, new in zip(old_rows, new_rows):
        seq = old[:5] + [BLANK] + old[5:10] + ([BLANK] + old[10:15] if len(old) > 10 else [])
        nseq = new[:5] + [BLANK] + new[5:10] + ([BLANK] + new[10:15] if len(new) > 10 else [])
        i = find(seq)
        if i < 0: continue
        for k, t in enumerate(nseq): hw[i + k] = (hw[i + k] & 0xfc00) | t
    if prompt_old:
        i = find(prompt_old)
        if i >= 0:
            for k in range(len(prompt_old)):
                t = prompt_new[k] if k < len(prompt_new) else BLANK
                hw[i + k] = (hw[i + k] & 0xfc00) | t
    # the <カタカナ・・・セレクトボタン> hint bar: both pages are now the same, so fill it with the bar tile
    i = find([0xb4, 0xb4, 0xa3])
    if i >= 0:
        j = i + 2
        while (hw[j] & 0x3ff) != 0xa4: hw[j] = (hw[j] & 0xfc00) | 0xb4; j += 1
        hw[j] = (hw[j] & 0xfc00) | 0xb4
    return struct.pack('<%dH' % len(hw), *hw)

def apply(rom, allrefs, game):
    k = KBD[game]
    conv = bytearray(rom.d[k['conv']:k['conv'] + k['convlen']])
    free = list(k['free'])
    def tile(c):
        try: return tile_for(c, conv, game)
        except KeyError:
            t = free.pop(0)
            conv[2 * t:2 * t + 2] = bytes([code_of(c, game), 0xff])
            return t
    blk, ln = lz77(rom.d, k['block'], limit=0x10000)
    blk = bytearray(blk)
    rows = [[tile(c) if c != ' ' else BLANK for c in row] for row in LAYOUT]
    prompt = [tile(c) if c != ' ' else BLANK for c in PROMPT]
    for s_, t_ in list(zip(''.join(LAYOUT), sum(rows, []))) + list(zip(PROMPT, prompt)):
        if s_ != ' ': blk[t_ * 32:(t_ + 1) * 32] = heart_tile() if s_ == '♥' else font_en.tile(s_)
    put_lz(rom, allrefs, k['block'], ln, bytes(blk))
    rom.w(k['conv'], bytes(conv))
    flat = bytes(x for r in rows for x in r)
    assert len(flat) == 85
    old = list(rom.d[k['table']:k['table'] + 85])
    old_rows = [old[i:i + 15] for i in range(0, 85, 15)]
    rom.w(k['table'], flat)
    for mo in k['maps']:
        m, mln = lz77(rom.d, mo, limit=0x10000)
        nm = patch_map(m, old_rows, rows, find_prompt(m, conv), prompt)
        put_lz(rom, allrefs, mo, mln, nm)
    # one page only: SELECT flips between identical copies
    for lst in ('mapptrs', 'tptrs'):
        first = bytes(rom.d[k[lst][0]:k[lst][0] + 4])
        for p in k[lst][1:]: rom.w(p, first)

def find_prompt(m, conv):
    # tiles for な ま え を に ゅ う り ょ く し て く だ さ い 。 (as in the Japanese map)
    want = [0x15, 0x1f, 0x03, 0x30, 0x16, 0x27, 0x02, 0x2b, 0x29, 0x07, 0x0b, 0x13, 0x07, 0x3c, 0x0a, 0x01, 0x98]
    hw = struct.unpack('<%dH' % (len(m) // 2), m)
    for i in range(len(hw) - len(want)):
        if all((hw[i + k] & 0x3ff) == want[k] for k in range(len(want))): return want
    return None

def put_lz(rom, allrefs, off, ln, data):
    c = lz77_compress(data)
    if len(c) <= ln:
        rom.w(off, c)
    else:
        a = rom.put(c, align=4)
        for ref in allrefs.get(off, []):
            rom.w(ref, struct.pack('<I', 0x08000000 + a))
