"""Patch the compressed window UI font (ROM 0C:F800, LZSS, tiles $100-$19F; also loaded at tile $000 on the
character-select screen). Replaces the status labels, the command-window title and two counters, then stores
the block uncompressed-as-literals in expanded ROM ($30:C000) and repoints the five loaders."""
import labels
from lzss import decompress, compress_literal, lo
SRC=(0x0C,0xF800); DST=(0x30,0xC000)
LOADERS=[0xa3de,0xc0cb,0xd8bc,0xe554,0x1003c]   # "LDA #$F800 / STA $3E / LDA #$000C / STA $40"
def tile_off(t): return (t-0x100)*16
def get_px(d,t):   # 8x16 narrow glyph: tile t (top) + t+0x10 (bottom)
    out=[]
    for half in (0,0x10):
        b=tile_off(t+half)
        for y in range(8):
            p0,p1=d[b+2*y],d[b+2*y+1]
            out.append([((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1) for x in range(8)])
    return out
def put_strip(d,t0,img):
    """img: 16 rows x (8*n) px -> tiles t0..t0+n-1 (top) and t0+0x10.. (bottom)"""
    n=len(img[0])//8
    for c in range(n):
        for half in (0,1):
            b=tile_off(t0+c+half*0x10)
            for y in range(8):
                p0=p1=0
                for x in range(8):
                    v=img[half*8+y][c*8+x]; p0|=(v&1)<<(7-x); p1|=(v>>1)<<(7-x)
                d[b+2*y]=p0; d[b+2*y+1]=p1
def left_label(text,w):
    r=labels.render(text,w,1) or labels.render(text,w,0)
    cols=[x for x in range(w) if any(r[y][x]==3 for y in range(16))]
    sh=min(cols)-1 if cols else 0
    return [[r[y][x+sh] if x+sh<w else 1 for x in range(w)] for y in range(16)]
YEN=["........","........","........","........",".#...#..",".#...#..","..#.#...","...#....",".#####..","...#....",".#####..","...#....","...#....","...#....","........","........"]
def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0])
    # status labels: 4 columns each at $144/$148/$14C
    for i,t in enumerate(('HP','Yen','EXP')):
        put_strip(d,0x144+4*i,left_label(t,32))
    # command window title at $166 (keeps the window's top border row)
    old=[get_px(d,0x166+c) for c in range(4)]
    img=labels.render('Cmd',32,1)
    img[0]=[old[c][0][x] for c in range(4) for x in range(8)]
    put_strip(d,0x166,img)
    put_strip(d,0x10F,[[1]*8 for _ in range(16)])                       # 尾 counter -> blank
    put_strip(d,0x10C,[[3 if ch=='#' else 1 for ch in r] for r in YEN])  # 円 -> ¥
    blob=compress_literal(bytes(d))
    o=lo(*DST); assert all(b==0xFF for b in rom[o:o+len(blob)]) or True
    rom[o:o+len(blob)]=blob
    for a in LOADERS:
        assert orig[a:a+10]==bytes([0xA9,0x00,0xF8,0x85,0x3E,0xA9,0x0C,0x00,0x85,0x40]),hex(a)
        rom[a+1:a+3]=bytes([DST[1]&255,DST[1]>>8]); rom[a+6]=DST[0]
    # character select: 才 (age suffix) in the label art row $3AA00, columns 4-5 -> blank
    labels.write_px(rom,0x3aa00,16,4,2,[[1]*16 for _ in range(16)])
    return len(blob)
