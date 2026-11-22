"""Fishing paper: the つり新聞 logo becomes FISH NEWS.

The paper screen's characters are LZSS $B1:995C (0x2000 bytes, 4bpp, tiles $300-$3FF, shared with other screens)
and its tilemap is LZSS $B1:F010 (32x32, loaded at $81:BE76). The logo is the box at tile columns 1-15,
rows 2-5 (palette 3: 7 frame, E orange, 1 outline, D ink); its 39 own tiles ($386-$3EF) plus the plain
orange tile $3FF fill the box. FISH NEWS is drawn in the same style and the box is re-tiled with those 39 tiles
(one per cell with ink, $3FF elsewhere), so the text is two tiles tall. Both blocks go in banks $80-$BF zero padding (VRAM-direct loader)."""
import struct
from PIL import Image, ImageFont, ImageDraw
import paths as P
from lzss import decompress, compress, lo
from field_signs import free_run
CH=(0xB1,0x995C); TM=(0xB1,0xF010)
BOX=(1,2,15,4)          # tile x, y, width, height
BG,EDGE,INK,BLANK=0xE,1,0xD,0x3FF
def tget(ch,t):
    o=(t-0x300)*32; return [[sum(((ch[o+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)]
def tput(ch,t,pix):
    o=(t-0x300)*32
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            for k in range(4): p[k]|=((pix[y][x]>>k)&1)<<(7-x)
        ch[o+2*y]=p[0]; ch[o+2*y+1]=p[1]; ch[o+16+2*y]=p[2]; ch[o+17+2*y]=p[3]
def art(W=112,H=14):
    f=ImageFont.truetype(P.font('DejaVuSans-Bold.ttf'),40); text='FISH NEWS'
    bb=f.getbbox(text); im=Image.new('1',(bb[2]-bb[0]+4,bb[3]-bb[1]+4),0)
    ImageDraw.Draw(im).text((2-bb[0],2-bb[1]),text,font=f,fill=1)
    im=im.crop(im.getbbox()).resize((W,H),Image.LANCZOS if False else Image.BILINEAR)
    return im
def canvas():
    bx,by,bw,bh=BOX; w,h=bw*8,bh*8
    m=art(); px=m.load(); W,H=m.size
    x0=(w-W)//2; y0=9                 # outline on rows 8-23: tile rows 3-4, 30 cells
    body={(x0+x,y0+y) for y in range(H) for x in range(W) if px[x,y]}
    cv=[[BG]*w for _ in range(h)]
    for (x,y) in body:
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                q=(x+dx,y+dy)
                if q not in body and 0<=q[0]<w and 0<=q[1]<h: cv[q[1]][q[0]]=EDGE
    for (x,y) in body: cv[y][x]=INK
    return cv
def apply(rom,orig):
    ch=bytearray(decompress(orig,lo(*CH))[0]); tm=bytearray(decompress(orig,lo(*TM))[0])
    assert len(ch)==0x2000 and len(tm)==0x800
    bx,by,bw,bh=BOX; own=[]
    for ty in range(by,by+bh):
        for tx in range(bx,bx+bw):
            e=struct.unpack_from('<H',tm,(ty*32+tx)*2)[0]; assert e&0xFC00==0x0C00,hex(e)
            if e&0x3FF!=BLANK and e&0x3FF not in own: own.append(e&0x3FF)
    assert tget(ch,BLANK)==[[BG]*8]*8 and len(own)==39,len(own)
    cv=canvas(); free=list(own)
    for ty in range(bh):
        for tx in range(bw):
            pix=[cv[ty*8+y][tx*8:tx*8+8] for y in range(8)]
            if pix==[[BG]*8]*8: t=BLANK
            else: t=free.pop(0); tput(ch,t,pix)
            struct.pack_into('<H',tm,((by+ty)*32+bx+tx)*2,0x0C00|t)
    out=[]
    for src,data in ((CH,ch),(TM,tm)):
        blob=compress(bytes(data)); o=free_run(rom,orig,len(blob)); rom[o:o+len(blob)]=blob
        bank=0x80|(o>>15); addr=0x8000|(o&0x7FFF); n=0
        pat=bytes([0xA9,src[1]&255,src[1]>>8,0x85,0x3E,0xA9,src[0],0x00,0x85,0x40]); i=orig.find(pat)
        while i>=0:
            rom[i+1:i+3]=bytes([addr&255,addr>>8]); rom[i+6]=bank; n+=1; i=orig.find(pat,i+1)
        out.append(('%02X:%04X'%(bank,addr),len(blob),n,len(free)))
    return out
if __name__=='__main__':
    cv=canvas(); print('\n'.join(''.join('%X'%v for v in r) for r in cv))
    print(sum(1 for ty in range(4) for tx in range(15) if any(cv[ty*8+y][tx*8+x]!=BG for y in range(8) for x in range(8))))
