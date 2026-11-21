"""Character-select panels: drop the 兄/妹/父/母 relation label and its colon, and move the name
(8 tiles) to the start of the row. Tilemap LZSS at 21:9674, loaded at 81:A664."""
from lzss import decompress, compress_literal, lo
SRC=(0x21,0x9674); DST=(0x38,0xD000); SITE=0xA664
def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0])
    W=lambda i:d[2*i]|d[2*i+1]<<8
    def S(i,v): d[2*i]=v&255; d[2*i+1]=v>>8
    n=0
    for lab in (0x180,0x182,0x184,0x186):
        idx=[i for i in range(len(d)//2) if W(i)&0x3FF==lab]
        assert len(idx) in (1,2),(hex(lab),idx)     # the map holds two identical screens
        for i in [j for x in idx for j in (x,x+32)]:
            assert W(i+2)&0x3FF in (0x020,0x030)
            names=[W(i+3+k) for k in range(8)]
            for k in range(8): S(i+k,names[k])
            for k in range(8,11): S(i+k,names[k-8]&0xFC00)   # blank tile, same palette as the name
        n+=1
    blob=compress_literal(bytes(d))
    o=lo(*DST); rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,0x74,0x96,0x85,0x3E,0xA9,0x21,0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    return len(blob)
