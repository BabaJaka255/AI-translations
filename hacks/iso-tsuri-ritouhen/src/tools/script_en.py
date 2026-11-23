"""Insert the English script (script/strings.json, script/tables.json) into the expanded ROM.

The text reader reads bank $E0, which starts as a copy of bank $C1. Fixed-width tables are rewritten in place in
$E0 (or moved, where English needs more room), '/'-terminated strings are written to free space at $E0:8000+ and
their pointers repointed.
"""
import os, json, textwrap
from textcodec import encode, columns
from inventory import STRINGS, TABLES

HERE = os.path.dirname(os.path.abspath(__file__)); GAME = os.path.dirname(HERE)
E0 = 0x200000
STORY_WIDTH = 28

def load(name):
    return json.load(open(os.path.join(GAME, 'script', name), encoding='utf-8'))

class Space:
    """Free space allocator in bank $E0 (16-bit addresses)."""
    def __init__(self, start, end): self.pc, self.end = start, end
    def alloc(self, n):
        a = self.pc; self.pc += n
        if self.pc > self.end: raise SystemExit('bank $E0 free space exhausted')
        return a

def fit(text, cols, align, nbsp=False):
    """Pad one table entry to cols columns."""
    if len(text) > cols: raise SystemExit('too long for %d columns: %r' % (cols, text))
    if nbsp: text = text.replace(' ', '{nbsp}')
    n = len(text.replace('{nbsp}', ' '))
    pad = cols - n
    if align == 'left': s = text + ' ' * pad
    elif align == 'right': s = ' ' * pad + text
    elif align.startswith('right-'):          # right-aligned with k trailing spaces
        k = min(pad, int(align[6:])); s = ' ' * (pad - k) + text + ' ' * k
    else: s = ' ' * (pad // 2) + text + ' ' * (pad - pad // 2)
    return encode(s)

from build import story_width
STORY_PX = 224      # bold proportional font, pixels 16-240 of each line

def wrap_px(p):
    lines, cur = [], ''
    for w in p.split(' '):
        t = (cur + ' ' + w) if cur else w
        if story_width(t) <= STORY_PX: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def story(text):
    out = bytearray()
    for para in text.rstrip('\n').split('\n'):
        p = para.strip()
        if p in ('{FFFC}', '{FFFD}'):
            out += encode(p); continue
        if p.startswith('{center}'):
            p = p[8:]; sp = story_width(' ')
            p = ' ' * ((STORY_PX - story_width(p)) // 2 // sp) + p
            out += encode(p) + b']'; continue
        if not p:
            out += b']'; continue
        for line in wrap_px(p):
            out += encode(line) + b']'
    return bytes(out + b']')

KEYBOARD = ['ABCDEFGHI', 'JKLMNOPQR', 'STUVWXYZ.', 'abcdefghi', 'jklmnopqr', 'stuvwxyz\'', '012345678', '9-!?&']

def keyboard():
    s = '>]]]  Enter your name.]]]]'
    rows = []
    for i, r in enumerate(KEYBOARD):
        line = '       ' + ' '.join('^' + c for c in r)
        if i == len(KEYBOARD) - 1:
            line += '   ^~End'
        rows.append(line)
    return encode(s + ']]'.join(rows), allow='>]^~')

def apply(rom, orig):
    S, T = load('strings.json'), load('tables.json')
    space = Space(0x8000, 0xFFFF)
    E = lambda a: E0 + (a & 0xFFFF)
    def put_string(addr, b):
        rom.put(E(addr), b + b'/')
    def repoint(key, new):
        for p in STRINGS[key][1]:
            rom.patch(p, '%02x%02x' % (STRINGS[key][0] & 0xff, STRINGS[key][0] >> 8), '%02x%02x' % (new & 0xff, new >> 8))

    # ---- '/'-terminated strings: relocate
    for key in STRINGS:
        if key == 'name_entry': b = keyboard()
        elif key in ('intro', 'ending'): b = story(S[key]['en'])
        else: b = encode(S[key]['en'], allow='>]^~<')
        a = space.alloc(len(b) + 1); put_string(a, b); repoint(key, a)

    # ---- fixed tables in place
    def inplace(key, align, nbsp=False):
        base, n, stride, cols, _ = TABLES[key]
        for e in T[key]['entries']:
            b = fit(e['en'], cols, align, nbsp)
            assert len(b) <= stride
            rom.put(E(base + e['i'] * stride), b)
    inplace('island_title', 'center')
    inplace('fish_title', 'center')
    # fish_title stride 17 but 16 columns: the 17th byte is the next entry's... fill it with '~' (no-op)
    for e in T['fish_title']['entries']:
        rom.d[E(0x6170 + e['i'] * 17 + 16)] = 0x7E
    inplace('method', 'left', nbsp=True)
    inplace('method2', 'center')
    inplace('bait', 'center')
    inplace('sub_spot', 'right-2', nbsp=True)
    inplace('spot', 'right-1' , nbsp=True)
    inplace('island', 'right', nbsp=True)
    # icon strings: letters A-M became codes 01-0D in the half-width table
    for a in range(0x71C8, 0x723F):
        c = rom.d[E(a)]
        if 0x41 <= c <= 0x4D: rom.d[E(a)] = c - 0x40

    # ---- record lines: cols 1-29, no rank digit, no "cm", spot+island 18 columns at a 32-byte stride
    tab = space.alloc(64 * 32)
    for e in T['record_spot']['entries']:
        rom.put(E(tab + e['i'] * 32), fit(e['en'], 18, 'left'))
    rom.patch(0x8A5C, '0200', '0100')                     # header column 2 -> 1
    rom.patch(0x8B7E, '0200', '0100')                     # record line column 2 -> 1
    rom.patch(0x8B0A, 'a504186931' + '20a28ba92020a28b', 'ea' * 13)   # drop "N " rank
    rom.patch(0x8B29, '08', '06')                         # name ends at column 6 (was 8 with the rank)
    rom.patch(0x8B73, '1c', '1d')                         # build line up to 29 columns
    rom.patch(0x8B94, '1c00', '1d00')                     # draw 29 columns
    rom.patch(0x8B4D, 'a96320a28ba96d20a28b', 'ea' * 10)  # drop "cm"
    rom.patch(0x8B67, 'bfe162c1', 'bf%02x%02xe0' % (tab & 0xff, tab >> 8))
    rom.patch(0x8B60, '0a0a0a0aaa', bytes([0x22]) + rom.labels['asl5'].to_bytes(3, 'little') + b'\xaa')

    # ---- fish name on the catch screen: 14 columns from col 9, 16-byte stride
    tab = space.alloc(20 * 16)
    for e in T['fish']['entries']:
        rom.put(E(tab + e['i'] * 16), fit(e['en'], 14, 'center'))
    rom.patch(0x9637, 'ade9070a0a8d9f040a186d9f0469606a',
              'ade9070a0a0a0a1869%02x%02x' % (tab & 0xff, tab >> 8) + 'ea' * 5)
    rom.patch(0x964B, '0a00', '0900')
    rom.patch(0x9657, '0c00', '0e00')

    # ---- angler list place: 8 columns
    tab = space.alloc(16)
    for e in T['place']['entries']:
        rom.put(E(tab + e['i'] * 8), fit(e['en'], 8, 'left'))
    rom.patch(0x8EF7, 'a772', '%02x%02x' % (tab & 0xff, tab >> 8))
    rom.patch(0x8F00, '0600', '0800')
    rom.patch(0x8F06, '0600', '0800')

    # ---- default record holder in fresh save data
    rom.patch(0x190E1, 'b2bfc0dbb3' + '20' * 7, fit(S['default_angler']['en'], 12, 'left'))

    # ---- label width measuring reads bank $E0 too
    rom.patch(0x981D, 'a9c1', 'a9e0')
    rom.patch(0x9836, 'a9c1', 'a9e0')
    # menu cursor sprite: sit exactly in the blank column left of the item (was 2 px further left)
    rom.patch(0x9055, 'faff', 'fcff')

    # ---- records-by-fish menu: slot -> fish id table (English menu is alphabetical per column)
    names = [e['en'] for e in T['fish_title']['entries']]
    slots = []
    for row in S['menu_by_fish']['en'].split(']'):
        slots += [x.strip() for x in row.split('^')[1:]]
    assert sorted(slots) == sorted(names), slots
    rom.put(E0 + 0x12200, bytes(names.index(n) for n in slots))
    rom.patch(0x89E0, '4a90041869' + '0a00', bytes([0x22]) + rom.labels['fishmap'].to_bytes(3, 'little') + b'\xea' * 3)
    print('script: $E0:8000-%04X used' % space.pc)
