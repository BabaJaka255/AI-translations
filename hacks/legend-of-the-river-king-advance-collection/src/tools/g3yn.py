# Game 3 Yes/No choice (control code FF). The handler DMAs the font glyphs は, い, え to tiles 300-302 and maps
# them as は い _ _ い い え. English: five tiles 'Yes' (2) and 'No' (3) are copied instead and the map writes
# get distinct tile numbers (300 301 _ _ 302 303 304).
import struct
from tilestr import render

LIT_SRC = [0x94f28, 0x94f34, 0x94f3c]          # DMA sources: font+は, font+い, font+え (tiles 300, 301, 302)
LIT_CNT = 0x94f30                              # shared DMA control 0x84000008 (8 words)
REUSE = [0x94eb4, 0x94ec0, 0x94ed2]            # ldrh r2,[r1] -> adds r2,#1 for the 3rd-5th map cells

def apply(rom):
    tiles = render('Yes', 2) + render('No', 3) + [b'\x11' * 32] * 2
    a = rom.put(b''.join(bytes(t) for t in tiles), align=4)
    old = [0x081b599c, 0x081b567c, 0x081b56bc]
    for k, (lit, o) in enumerate(zip(LIT_SRC, old)):
        assert struct.unpack_from('<I', rom.d, lit)[0] == o
        rom.w(lit, struct.pack('<I', 0x08000000 + a + 32 * k))
    assert struct.unpack_from('<I', rom.d, LIT_CNT)[0] == 0x84000008
    rom.w(LIT_CNT, struct.pack('<I', 0x84000028))
    for p in REUSE:
        assert rom.d[p:p + 2] == b'\x0a\x88'
        rom.w(p, struct.pack('<H', 0x3201))
