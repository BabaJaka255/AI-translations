"""English keyboard for the character name-entry screen (bank 1 AF2E-B5DE).

Grid: 10 columns x 11 rows of letter cells (row 0 = buttons).
  cells 0-47  -> 'kana' block, VRAM word $2A00 (48 x 16x16 glyph slots)
  cells 48-109 -> 'kanji' block, VRAM word $3000 (slot = cell-48)
Glyph slots use the staging layout: 8 glyphs per 0x200-byte line, TL/TR at +0/+0x10, BL/BR at +0x100/+0x110.
Instead of drawing the Japanese palette strings, we DMA pre-rendered blocks from ROM and point the
selection code at our own one-byte-per-cell tables."""
BANK=0x38
BASE=(BANK-0x30)*0x8000+0x180000
KANA_A=0x8000; KANJI_A=0x8C00; T1_A=0x9C00; T2_A=0x9C80; CODE_A=0x9D00

ROWS=[
 "ABCDEFGHIJ",
 "KLMNOPQRST",
 "UVWXYZ.,'\"",
 "abcdefghij",
 "klmnopqrst",
 "uvwxyz!?- ",
 "0123456789",
 "&()/:;+*=#",
 "~@%$^_<>[]",
 "{}|\\`     ",
 "          ",
]
CELLS=''.join(ROWS); assert len(CELLS)==110

def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)

def glyph_block(chars,glyph):
    """chars: list of characters for slots; glyph(c)-> 16 rows of 8-bit ints."""
    n=len(chars); size=((n+7)//8)*0x200
    out=bytearray(size)
    for i in range(0,size,2): out[i]=0xFF          # background colour 1 (plane 0 set)
    for k,c in enumerate(chars):
        rows=glyph(c)
        line=(k//8)*0x200; col=(k%8)*0x20
        for y in range(16):
            v=rows[y]<<4                            # centre 8px glyph in 16px cell
            L,R=(v>>8)&0xFF,v&0xFF
            half=0x100 if y>=8 else 0; yy=y&7
            for t,b in ((0,L),(0x10,R)):
                o=line+half+col+t+2*yy
                out[o+1]|=b                         # ink = colour 3 (plane 0 already 1)
    return bytes(out)

def apply(rom,orig,glyph):
    kana=glyph_block(list(CELLS[:48]),glyph); assert len(kana)==0xC00
    kanji=glyph_block(list(CELLS[48:110]),glyph); assert len(kanji)==0x1000
    rom[BASE:BASE+0xC00]=kana
    rom[BASE+0xC00:BASE+0x1C00]=kanji
    # selection tables
    t1=bytearray(0x80)
    for i in range(50):
        t1[i if i<48 else i+1]=ord(CELLS[i])
    t2=bytearray(0x80)
    for r in range(6,11+1):
        for c in range(10):
            t2[(r-6)*20+c*2+2]=ord(CELLS[(r-1)*10+c])
    rom[lo(BANK,T1_A):lo(BANK,T1_A)+0x80]=t1
    rom[lo(BANK,T2_A):lo(BANK,T2_A)+0x80]=t2
    # helpers: set [$0A] -> table, mimic B6EA's $084E=3
    def helper(tab):
        return bytes([0xA9,tab&255,tab>>8,0x85,0x0A, 0xA9,BANK,0x00,0x85,0x0C,
                      0xA9,0x03,0x00,0x8D,0x4E,0x08, 0x6B])
    h1=CODE_A; c1=helper(T1_A); h2=h1+len(c1); c2=helper(T2_A)
    rom[lo(BANK,h1):lo(BANK,h1)+len(c1)]=c1
    rom[lo(BANK,h2):lo(BANK,h2)+len(c2)]=c2
    JSL=lambda a:bytes([0x22,a&255,a>>8,BANK])
    def hk(bank,addr,old,new):
        o=lo(bank,addr); assert orig[o:o+len(old)]==old,(hex(addr),orig[o:o+len(old)].hex());
        assert len(new)<=len(old); rom[o:o+len(old)]=new+b'\xEA'*(len(old)-len(new))
    hk(1,0xB518,bytes.fromhex('a0140020eab6'),JSL(h1))
    hk(1,0xB562,bytes.fromhex('a0160020eab6'),JSL(h2))
    hk(1,0xB56A,bytes.fromhex('a01a0020eab6'),JSL(h2))
    # kanji-area copy: write one byte + terminator only
    hk(1,0xB578,bytes.fromhex('b70a9d6a08c8b70a9d6b08a9009d6c08'),bytes.fromhex('b70a9d6a08a9009d6b08'))
    # palettes: DMA pre-rendered blocks instead of drawing strings
    def dma(vram,src,size,ret):
        return bytes([0xA9,vram&255,vram>>8,0x85,0x46, 0xA9,src&255,src>>8,0x85,0x42,
                      0xA9,BANK,0x00,0x85,0x44, 0xA9,size&255,size>>8,0x85,0x3E,
                      0x22,0x52,0xDA,0x00, 0x4C,ret&255,ret>>8])
    o=lo(1,0xAF2E); assert orig[o:o+6]==bytes.fromhex('a0140020eab6')
    code=dma(0x2A00,KANA_A,0xC00,0xAF5F); rom[o:o+len(code)]=code
    o=lo(1,0xAF5F); assert orig[o:o+3]==bytes.fromhex('ad6008')
    code=dma(0x3000,KANJI_A,0x1000,0xAFA0); rom[o:o+len(code)]=code
    assert orig[lo(1,0xAFA0):lo(1,0xAFA0)+3]==bytes.fromhex('a9d49c')
    # name length 4 -> 8
    hk(1,0xB38C,bytes.fromhex('c90400'),bytes.fromhex('c90800'))
    # cursor: x = min(count,7)*8 + 8
    hk(1,0xB3E6,bytes.fromhex('c90400d003a90300'),bytes.fromhex('c90800d003a90700'))
    hk(1,0xB3EE,bytes.fromhex('0a0a0a0a'),bytes.fromhex('0a0a0aEA'))
    # button row: skip the (now unused) dakuten/handakuten buttons (cols 5,6) -> min col 7
    hk(1,0xB18D,bytes.fromhex('c90500b007a90500'),bytes.fromhex('c90700b007a90700'))
    # and make them inert anyway (error beep) in case they are reached
    hk(1,0xB457,bytes.fromhex('201bb4'),bytes.fromhex('4c78b4'))
    hk(1,0xB486,bytes.fromhex('201bb4'),bytes.fromhex('4ca8b4'))
    # names are stored without the English marker: force English rendering wherever a name is drawn
    hk(1,0xB596,bytes.fromhex('a90000850c'),bytes.fromhex('a90001850c'))
    hk(1,0xAFD0,bytes.fromhex('a90000850c'),bytes.fromhex('a90001850c'))
    hk(2,0x874F,bytes.fromhex('a90000850c'),bytes.fromhex('a90001850c'))
    for a in (0xa526,0xa585,0xa5d1,0xa61d,0xdba6,0xe14d,0xe5e0,0xe5f2,0xe604,0xe616,0xf541,0xf882):
        o=a; assert orig[o:o+5]==bytes.fromhex('a97000850c'),hex(a)
        rom[o:o+5]=bytes.fromhex('a97001850c')

def secret_name(rom,orig,name=b'FishTaro'):
    """The brother's hidden name つり太郎 ("Tsuri Taro", the developers' earlier fishing game) unlocks a
    stocked inventory (81:B077 compares 8 bytes of the name with 01:B0F0). English keyboard version."""
    assert orig[0xB0F0:0xB0F8]==bytes.fromhex('2f55e044e0220000') and len(name)<=8
    rom[0xB0F0:0xB0F8]=name.ljust(8,b'\0')
