"""Fishing Note contents page. The page tilemap (LZSS at 21:A67F -> 7F:B800) references the glyph tiles that
string #53 is drawn into (tiles $140-$19F, 16 columns per staging line, one column per English character).
We rewrite the tilemap so each label points at its English characters and store it in expanded ROM."""
from lzss import decompress, compress_literal, lo
SRC=(0x21,0xA67F); DST=(0x30,0xD000); SITE=0xCE3B
# (label, Japanese glyph columns used by the original layout as (first tile, number of columns))
PARTS=[('Fish Notes',0x140,10),('Index',0x14A,6),('Stream',0x160,4),('Alpine',0x164,6),('Creek',0x16A,4),
       ('Lake',0x16E,2),('Plains',0x180,4),('Coast',0x184,4)]
TEXT=''.join(p[0] for p in PARTS)       # string #53 (47 columns)
def col_tile(c): return 0x140+(c//16)*0x20+(c%16)
def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0])
    W=lambda i:d[2*i]|d[2*i+1]<<8
    def S(i,v): d[2*i]=v&255; d[2*i+1]=v>>8
    pos={}
    for text,t0,n in PARTS:   # locate every label in the untouched map first
        idx=[i for i in range(len(d)//2) if W(i)&0x3FF==t0]
        assert len(idx)==1,(text,hex(t0),idx)
        pos[t0]=(idx[0],W(idx[0])&0xFC00)
    start=0
    for text,t0,n in PARTS:
        i,attr=pos[t0]
        for k in range(max(n,len(text))):
            top=i+k; bot=i+32+k
            if k<len(text):
                tt=col_tile(start+k); S(top,attr|tt); S(bot,attr|(tt+0x10))
            else:
                S(top,0); S(bot,0)
        start+=len(text)
    blob=compress_literal(bytes(d))
    o=lo(*DST); rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,0x7F,0xA6,0x85,0x3E,0xA9,0x21,0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    return len(blob)
