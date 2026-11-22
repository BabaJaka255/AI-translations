"""Town building plaques (宿 inn, 魚 fish shop, 釣 tackle shop), as in Kawa no Nushi Tsuri 2.
The town tileset is LZSS $91:856B (0x7800 bytes, 4bpp), named by three entries of the area tileset
table at ROM $1902 (+$18, +$28). Each plaque is a 16x16 frame: top tiles F5/F6, F7/F8, F9/FA, bottom
tiles 100/101, 102/103, 104/105. The 12x12 interior (black, colour 1) gets INN as text and a fish and
a hook as pictures, in white (F), with no shadow (colour 6 is the frame's gold here).
The loader ($80:98F0) writes VRAM directly, so the block goes in zero padding of banks $80-$BF."""
import struct
from lzss import decompress, compress, lo
SRC=(0x91,0x856B); TABLE=[0x1902,0x191A,0x192A]
PLAQUES={'inn':(0xF5,0xF6,0x100,0x101),'fish':(0xF7,0xF8,0x102,0x103),'tackle':(0xF9,0xFA,0x104,0x105)}
INK,BG=0xF,1
ART={
'inn':[
"            ",
"            ",
"            ",
" # #  # #  #",
" # ## # ## #",
" # ## # ## #",
" # # ## # ##",
" # # ## # ##",
" # #  # #  #",
"            ",
"            ",
"            "],
'fish':[
"            ",
"            ",
"            ",
"     ###    ",
" #  ######  ",
" ########## ",
" ####### ###",
" ########## ",
" #  ######  ",
"     ###    ",
"            ",
"            "],
'tackle':[
"     ###    ",
"     # #    ",
"     ###    ",
"      #     ",
"      #     ",
"      #     ",
" #    #     ",
" ##   #     ",
" #    #     ",
" #   #      ",
"  ###       ",
"            "],
}
def get(d,t): return [[sum(((d[t*32+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)]
def put(d,t,pix):
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            for k in range(4): p[k]|=((pix[y][x]>>k)&1)<<(7-x)
        d[t*32+2*y]=p[0]; d[t*32+2*y+1]=p[1]; d[t*32+16+2*y]=p[2]; d[t*32+17+2*y]=p[3]
def free_run(rom,orig,n):
    for bank in (0xB4,0xB5,0xBF):
        base=lo(bank,0x8000); z=0
        for i in range(base,base+0x8000):
            z=z+1 if rom[i]==0 and orig[i]==0 else 0
            if z==n+32: return i-z+1+16
    raise SystemExit('no room for the town tileset')
def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==0x7800
    for name,q in PLAQUES.items():
        img=[[0]*16 for _ in range(16)]
        for t,ox,oy in zip(q,(0,8,0,8),(0,0,8,8)):
            for y,row in enumerate(get(d,t)): img[oy+y][ox:ox+8]=row
        assert img[0]==[0xA]*16 and img[2][2:14]==[BG]*12,name      # the frame is where we expect it
        art=ART[name]
        for y in range(12):
            for x in range(12): img[2+y][2+x]=BG
        for y in range(12):
            for x in range(12):
                if art[y][x]=='#':
                    img[2+y][2+x]=INK
        for t,ox,oy in zip(q,(0,8,0,8),(0,0,8,8)): put(d,t,[img[oy+y][ox:ox+8] for y in range(8)])
    blob=compress(bytes(d)); o=free_run(rom,orig,len(blob))
    rom[o:o+len(blob)]=blob
    bank=0x80|(o>>15); addr=0x8000|(o&0x7FFF)
    for e in TABLE:
        assert orig[e:e+4]==bytes([SRC[1]&255,SRC[1]>>8,SRC[0],0])
        rom[e:e+4]=bytes([addr&255,addr>>8,bank,0])
    return '%02X:%04X'%(bank,addr),len(blob)
