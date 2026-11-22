"""Fish names in the "[fish] landed!" message (fishing overlay, sector 990 loaded at $8000).

$8254: name = area base (by $27e5: $8759/$87D1/$883D/$88B1/$8927) + offset byte from $871E[fish].
Names end with the word D0D0, which continues with the sub-string chosen by $26D0 (" landed!" etc.).
The table has 5 areas x 12 slots (the last area 11); names may be shared between slots of an area.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from fish_guide import FISH

SECTOR = 990
OFFS = 0x871E; NSLOT = 59
LIST = (0x8759, 0x8983)                       # name area
TAIL = (0x9D6E, 0xA000)                       # zero padding at the end of the 8 KB chunk
BASE_CODE = (0x8263, 0x826E, 0x8279, 0x8284, 0x828B)   # ldx #hi / ldy #lo for each area
EXTRA = {'イモリ': 'Newt', 'カエル': 'Frog', 'モロコ': 'Gudgeon', 'カナヘビ': 'Lizard', 'カメ': 'Turtle',
         'テナガエビ': 'River Prawn', 'ヘビ': 'Snake', 'カワノヌシ': 'River King'}

def rebuild(t):
    chunk = bytearray(b''.join(t.read(SECTOR + i) for i in range(4)))
    def at(a): return a - 0x8000
    def name(a):
        s = b''
        while chunk[at(a):at(a) + 2] != b'\xd0\xd0': s += bytes([chunk[at(a) + 1], chunk[at(a)]]); a += 2
        return s.decode('cp932')
    bases = []
    for p in BASE_CODE:
        c = chunk[at(p):at(p) + 4]; assert c[0] == 0xA2 and c[2] == 0xA0, hex(p)
        bases.append(c[1] << 8 | c[3])
    offs = chunk[at(OFFS):at(OFFS) + NSLOT]
    areas = [list(range(a * 12, min(a * 12 + 12, NSLOT))) for a in range(5)]
    for a, slots in enumerate(areas):
        jp = [name(bases[a] + offs[i]) for i in slots]
        areas[a] = (slots, jp)
    chunk[at(LIST[0]):at(LIST[1])] = bytes(LIST[1] - LIST[0])
    regions = [list(LIST), list(TAIL)]
    def blob(j):
        en = (FISH.get(j) or EXTRA[j]).encode('ascii')
        return (b' ' + en if len(en) % 2 else en) + b'\xd0\xd0'   # odd: leading space, as for animals
    for a, (slots, jp) in enumerate(areas):
        uniq = list(dict.fromkeys(jp)); size = sum(len(blob(j)) for j in uniq)
        r = next(r for r in regions if r[0] + size <= r[1])
        base = p = r[0]; placed = {}
        for j in uniq:
            b = blob(j); placed[j] = p - base; chunk[at(p):at(p) + len(b)] = b; p += len(b)
        assert p - base <= 256, a
        r[0] = p
        for i, j in zip(slots, jp): chunk[at(OFFS) + i] = placed[j]
        bp = BASE_CODE[a]; chunk[at(bp) + 1] = base >> 8; chunk[at(bp) + 3] = base & 0xFF
    for i in range(4): t.write(SECTOR + i, 0, bytes(chunk[i * 2048:(i + 1) * 2048]))
    return [hex(r[0]) for r in regions]
