"""English keyboard for the postcard message screen (bank 1 E7EE / EDxx-F480).

The screen has three palette modes cycled by a button (originally hiragana / katakana / kanji).
They become UPPER / lower / symbols. Each palette is 50 cells (rows 2-6 x 10 cols), drawn as 56 16x16
glyph slots in staging layout and DMA'd to VRAM word $3400; we DMA pre-rendered blocks instead.
The message is stored without an English marker and is always drawn in English mode."""
from name_entry import glyph_block, lo
BANK=0x38
BLK=[0xA000,0xAE00,0xBC00]          # mode 0 / 1 / 2 blocks (0xE00 each)
TAB=[0xCA00,0xCA40,0xCA80]
CODE=0xCC00
SYM='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
MODES=[
 ["ABCDEFGHIJ","KLMNOPQRST","UVWXYZ'\"()","&/:;+*=#%@","<>[]$^_~  "],
 ["abcdefghij","klmnopqrst","uvwxyz'\"()","&/:;+*=#%@","<>[]$^_~  "],
 [SYM[0:10],SYM[10:20],SYM[20:30],SYM[30:]+' '*8,' '*10],
]
def apply(rom,orig,glyph):
    for m,rows in enumerate(MODES):
        cells=''.join(rows); assert len(cells)==50,(m,len(cells))
        blk=glyph_block(list(cells)+[' ']*6,glyph); assert len(blk)==0xE00
        o=lo(BANK,BLK[m]); rom[o:o+0xE00]=blk
        o=lo(BANK,TAB[m]); rom[o:o+50]=cells.encode()
    def hk(addr,old,new):
        old=bytes.fromhex(old); o=lo(1,addr); assert orig[o:o+len(old)]==old,(hex(addr),orig[o:o+len(old)].hex())
        new=bytes.fromhex(new) if isinstance(new,str) else new
        assert len(new)<=len(old); rom[o:o+len(new)]=new
    # selection: point [$0A] at our one-byte tables (mode 0/1/2 = Y $1C/$1E/$20)
    c=CODE; jsl=[]
    for m in range(3):
        code=bytes([0xA9,TAB[m]&255,TAB[m]>>8,0x85,0x0A,0xA9,BANK,0x00,0x85,0x0C,0xA9,0x03,0x00,0x8D,0x4E,0x08,0x6B])
        rom[lo(BANK,c):lo(BANK,c)+len(code)]=code; jsl.append(c); c+=len(code)
    J=lambda a:bytes([0x22,a&255,a>>8,BANK,0xEA,0xEA])
    hk(0xF421,'a01c0020eab6',J(jsl[0])); hk(0xF42F,'a01e0020eab6',J(jsl[1])); hk(0xF43D,'a0200020eab6',J(jsl[2]))
    hk(0xF44F,'f014','eaea')                       # mode 2 also reads one byte
    # palette drawing: mode switch draws the NEXT mode's palette
    def src(a): return bytes([0xA9,a&255,a>>8,0x85,0x42,0x4C,0x03,0xF3,0xEA])
    hk(0xF2DE,'a01e0020eab64c03f3',src(BLK[1]))
    hk(0xF2EC,'a0200020eab64c03f3',src(BLK[2]))
    hk(0xF2FA,'a01c0020eab64c03f3',src(BLK[0]))
    def raw(addr,old,new,end):
        old=bytes.fromhex(old); o=lo(1,addr); assert orig[o:o+len(old)]==old,hex(addr)
        assert len(new)<=end-addr; rom[o:o+len(new)]=new
    # $42 = block (set above); $46 = VRAM $3400, $44 = bank, size $E00, DMA, continue at F32E
    raw(0xF303,'a9000085',bytes.fromhex('a9003485'+'46'+'a9380085'+'44'+'a9000e85'+'3e'+'226ada00'+'4c2ef3'),0xF32E)
    # initial palette (mode 0)
    raw(0xE7EE,'a01c0020eab6',bytes([0xA9,0x00,0x34,0x85,0x46,0xA9,BLK[0]&255,BLK[0]>>8,0x85,0x42,0xA9,BANK,0x00,0x85,0x44,
        0xA9,0x00,0x0E,0x85,0x3E,0x22,0x52,0xDA,0x00,0x4C,0x1F,0xE8]),0xE81F)
    assert orig[lo(1,0xE81F):lo(1,0xE81F)+3]==bytes.fromhex('20ebe9')
    # fixed keys store ASCII
    hk(0xEDA9,'a9ac','a93f')   # ?
    hk(0xEDCC,'a9ab','a921')   # !
    hk(0xEDEF,'a90d','a92c')   # ,
    hk(0xEE12,'a90e','a92e')   # .
    hk(0xEF1D,'a90c','a920')   # space
    hk(0xF0FD,'a9aa','a92d')   # -
    # digit keys (row 1, cols 2-11) store ASCII '0'-'9' instead of the Japanese digit glyphs
    dg=c; code=bytes([0xAF,0x30,0x2C,0x7F,0x18,0x69,0x2E,0x6B])   # (8-bit A) LDA col / CLC / ADC #$2E / RTL
    rom[lo(BANK,dg):lo(BANK,dg)+len(code)]=code; c+=len(code)
    hk(0xF11A,'af302c7f3a',bytes([0x22,dg&255,dg>>8,BANK,0xEA]))
    # dakuten / handakuten keys: always refuse
    hk(0xEE2B,'af3a2c','4c82ee')
    hk(0xEE90,'af3a2c','4c82ee')
    # width counting: ASCII counts as one half-width unit
    hk(0xF018,'c90f','c980')
    # draw the message in English mode
    for a in (0xEA2E,0xEA81,0xF19E,0xF222):
        hk(a,'a97f00850c','a97f01850c')
