"""Character-select panels. String 3 (弟姉父母年齢才最初から始める) is drawn into glyph tiles $180- (16 columns
per staging line), and the panel tilemap (LZSS $90:AC59, two screens, loaded at ROM 0x909F) points at them.
As on the contents page, string 3 becomes a pool of letters and the tilemap spells the English labels.
Each panel row becomes  Bro:Ichiro / Age:12 / New Game."""
from lzss import decompress, compress, lo
SRC=(0x90,0xAC59); DST=(0xF2,0xA000); SITE=0x909F
# String 3 is drawn in pieces that start inside it: 弟姉父母 (8 tiles from $180), 年齢 and 才 (6 from $188),
# 最初から始める (14 from $18E). Each piece gets its own English entry of the same width, and the labels are
# spelled from those tiles.
SEGS={0:'BroSisDa',8:'AgedMm',12:'Mm',14:'   New Game   '}   # byte offset in string 3 -> English
TILE0={0:0x180,8:0x188,12:0x18C,14:0x18E}
def col_tile(c): return 0x180+(c//16)*0x20+(c%16)
def tile_of(seg,k):
    c=(TILE0[seg]-0x180)+k          # staging column of letter k of that piece
    return col_tile(c)
POOL={}
for seg in (0,8,14):
    for k,ch in enumerate(SEGS[seg]): POOL.setdefault(ch,tile_of(seg,k))
REL={0x180:'Bro',0x182:'Sis',0x184:'Dad',0x186:'Mom'}
AGE='Age'; START='New Game'
def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0])
    o=bytes(d)
    W=lambda i:o[2*i]|o[2*i+1]<<8          # always read the untouched map
    def S(i,v): d[2*i]=v&255; d[2*i+1]=v>>8
    def spell(i,text,width,attr):
        for k in range(width):
            c=text[k] if k<len(text) else ' '
            if c==' ': S(i+k,attr); S(i+32+k,attr)
            else:
                t=POOL[c]; S(i+k,attr|t); S(i+32+k,attr|(t+0x10))
    n=0
    for i in range(len(d)//2-40):
        t=W(i)&0x3FF; attr=W(i)&0xFC00
        if t in REL and W(i+1)&0x3FF==t+1 and W(i+2)&0x3FF==0x020:
            name=[W(i+3+k) for k in range(8)]; nameb=[W(i+35+k) for k in range(8)]
            colon=(W(i+2),W(i+34))
            spell(i,REL[t],3,attr)
            S(i+3,colon[0]); S(i+35,colon[1])
            for k in range(8): S(i+4+k,name[k]); S(i+36+k,nameb[k])
            n+=1
        elif t==0x188 and W(i+1)&0x3FF==0x189:
            spell(i,AGE+' ',4,attr)
            for k in range(4,9):
                if W(i+k)&0x3FF in (0x18C,0x18D): S(i+k,attr); S(i+32+k,attr)
        elif t==0x18E and W(i+1)&0x3FF==0x18F:
            pass                                                 # 最初から始める: same tiles, English piece
    assert n==8,n
    blob=compress(bytes(d))
    o=lo(*DST); rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,SRC[1]&255,SRC[1]>>8,0x85,0x3E,0xA9,SRC[0],0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    return len(blob)
