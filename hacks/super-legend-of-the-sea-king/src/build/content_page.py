"""Fishing Note contents page. The page tilemap (LZSS $90:C057, loaded at ROM 0xB7F5) points at the glyph
tiles that string 14 is drawn into (tiles $140-, 16 columns per staging line, one column per English
character). Only 48 columns (three staging lines) get drawn, so string 14 becomes a pool of the distinct
letters the labels use, and the rewritten tilemap spells every label out of that pool."""
from lzss import decompress, compress, lo
SRC=(0x90,0xC057); DST=(0xF2,0x8000); SITE=0xB7F5
# (English, first tile of the Japanese label, its width in columns)
PARTS=[('Fishing Note',0x140,10),('Contents',0x14A,6),('Breakwater',0x160,6),('Beach',0x166,4),('Rocks',0x16A,2),
       ('Coast',0x16C,4),('Islet',0x180,4),('Open Sea',0x184,4),('Far Isle',0x188,4)]
TEXT=''.join(dict.fromkeys(c for p in PARTS for c in p[0] if c!=' '))   # string 14
assert len(TEXT)<=48,len(TEXT)
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
    for text,t0,n in PARTS:
        i,attr=pos[t0]
        for k in range(max(n,len(text))):
            top=i+k; bot=i+32+k
            if k<len(text) and text[k]!=' ':
                tt=col_tile(TEXT.index(text[k])); S(top,attr|tt); S(bot,attr|(tt+0x10))
            else:
                S(top,0); S(bot,0)
    blob=compress(bytes(d))
    o=lo(*DST); rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,SRC[1]&255,SRC[1]>>8,0x85,0x3E,0xA9,SRC[0],0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    return len(blob)
