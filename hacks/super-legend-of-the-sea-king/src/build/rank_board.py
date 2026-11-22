"""Cup ranking board (81:D380). The cup title (strings 23-29) is drawn into tiles $140-, the header string 22
順位名前記録 into tiles $160- (16 columns, one per English character), and the board tilemaps (LZSS $90:C45F
and $90:C6B0, pointers at $81:D976, 7 cups) reuse the header's 位 (tiles $162/$163) after each rank digit.
String 22 becomes "RankNameRecord." and the maps are re-tiled: Rank cols 6-9, Name cols 11-14, Record cols
19-24 over "cm" (17-22 on the count boards, whose unit tile $0F is blank), and each rank digit is followed by the full stop (column 14 of the header run)."""
import struct
from lzss import decompress, compress, lo
from field_signs import free_run
TEXT='RankNameRecord.'
TABLE=0x8000+(0xD976-0x8000)          # ROM offset of $81:D976
LABELS=[(6,0,4),(11,4,4),(19,8,6)]    # (tilemap column, first header column, letters)
DOT=14
def retile(d):
    W=list(struct.unpack('<1024H',d))
    hdr=[x for x in range(32) if W[32*9+x]&0x3FF==0x160]; assert hdr==[6],hdr
    attr=W[32*9+6]&0xFC00
    count=any(W[32*y+x]&0x3FF==0x0F for y in range(11,23) for x in range(32))
    for x in range(32): W[32*9+x]=W[32*10+x]=0
    for col,c0,n in LABELS:
        if c0==8 and count: col-=2
        for k in range(n):
            W[32*9+col+k]=attr|(0x160+c0+k); W[32*10+col+k]=attr|(0x170+c0+k)
    for y in range(11,23):
        for x in range(31):
            if W[32*y+x]&0x3FF in (0x162,0x172):
                a=W[32*y+x]&0xFC00; top=W[32*y+x]&0x3FF==0x162
                W[32*y+x]=a|((0x160 if top else 0x170)+DOT); W[32*y+x+1]=0
    return struct.pack('<1024H',*W)
def apply(rom,orig):
    ptrs=[struct.unpack('<HH',orig[TABLE+4*i:TABLE+4*i+4]) for i in range(7)]
    new={}
    for a,b in sorted(set(ptrs)):
        d=decompress(orig,lo(b,a))[0]; assert len(d)==2048
        blob=compress(retile(d)); o=free_run(rom,orig,len(blob)); rom[o:o+len(blob)]=blob
        new[(a,b)]=(0x8000|(o&0x7FFF),(o>>15)|0x80)
    for i,p in enumerate(ptrs): rom[TABLE+4*i:TABLE+4*i+4]=struct.pack('<HH',*new[p])
    return ['%02X:%04X'%(b,a) for a,b in new.values()]
