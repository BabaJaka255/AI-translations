"""Title screen: replace the 川のぬし釣り2 logo and the はじめる sprite with English art.

The title graphics block (LZSS at 1E:EFE5, loaded at 81:9819 to VRAM word $2000) also holds the sprite
tiles (OBJ base = VRAM word $6000 -> block offset $8000 + tile*32, 4bpp).
Logo = sprite group 01:9B08: 32x32 sprites (tiles 0,4,8,C,100,104) on top, 16x16 sprites below,
forming a 192x48 picture. Start label = group 01:9CD0, four 16x16 sprites (tiles 160-166).
Palette (OBJ palette 0): 2..7 red->yellow gradient, 10 pink highlight, 13 gold edge, 15 white outline,
9 white, 12 green, 14 grey."""
import paths as P
from PIL import Image, ImageFont, ImageDraw
from lzss import decompress, compress_literal, lo
SRC=(0x1E,0xEFE5); DST=(0x39,0x8000); SITE=0x9819
FONT=P.font('DejaVuSans-Bold.ttf')
W,H=192,48

def mask_text(text,size,stretch=1.0,font=FONT):
    f=ImageFont.truetype(font,size); bb=f.getbbox(text)
    im=Image.new('1',(bb[2]-bb[0]+4,bb[3]-bb[1]+4),0)
    ImageDraw.Draw(im).text((2-bb[0],2-bb[1]),text,font=f,fill=1)
    if stretch!=1.0: im=im.resize((int(im.size[0]*stretch),im.size[1]),Image.NEAREST)
    return im.crop(im.getbbox())

def place(m,x,y,w,h):
    if x=='c': x=(w-m.size[0])//2
    pxm=m.load(); body=set()
    for yy in range(m.size[1]):
        for xx in range(m.size[0]):
            if pxm[xx,yy] and 0<=x+xx<w and 0<=y+yy<h: body.add((x+xx,y+yy))
    return body,y,y+m.size[1]-1

def style(img,body,y0,y1):
    bands=[2,3,4,5,6,7]
    nb=lambda x,y:[(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]
    for (x,y) in body:
        t=(y-y0)/max(1,y1-y0); v=bands[min(5,int(t*6))]
        if (x+1,y) in body and (x+2,y) not in body and (x,y-1) in body: v=10
        if t>0.6 and any(p not in body for p in nb(x,y)): v=13
        img[y][x]=v
    for (x,y) in body:
        for (px,py) in nb(x,y):
            if (px,py) not in body and 0<=px<W and 0<=py<H and img[py][px]==0: img[py][px]=15

def logo_image():
    img=[[0]*W for _ in range(H)]
    for text,size,y,st in (('SUPER',21,1,1.1),('RIVER KING',40,17,0.74)):
        b,y0,y1=place(mask_text(text,size,st),'c',y,W,H); assert all(x<W-1 for x,_ in b)
        style(img,b,y0,y1)
    return img

def start_image():
    w,h=64,16; img=[[0]*w for _ in range(h)]
    b,_,_=place(mask_text('START',13,1.15),'c',2,w,h)
    for (x,y) in b:
        img[y][x]=9
    for (x,y) in b:
        if (x+1,y+1) not in b and x+1<w and y+1<h and img[y+1][x+1]==0: img[y+1][x+1]=14
    return img

def put_tile(d,n,pix):
    o=0x8000+n*32
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            v=pix[y][x]
            for k in range(4): p[k]|=((v>>k)&1)<<(7-x)
        d[o+2*y]=p[0]; d[o+2*y+1]=p[1]; d[o+16+2*y]=p[2]; d[o+17+2*y]=p[3]

def blit(d,img,tn,x0,y0,size):
    for ty in range(size):
        for tx in range(size):
            put_tile(d,tn+ty*16+tx,[[img[y0+ty*8+y][x0+tx*8+x] for x in range(8)] for y in range(8)])

PAL_ROM=0x3FBC0     # OBJ palette 0 (07:FBC0), used only by the logo and START on the title
def snes(c): r,g,b=c; return (r>>3)|((g>>3)<<5)|((b>>3)<<10)
CUSTOM=P.b('logo_custom.png')
def load_png(path):
    """192x48 PNG -> (index rows, {index: rgb}). Transparent = alpha<128 or #FF00FF. Max 15 colours
    (more are reduced); colours snap to the SNES 15-bit grid."""
    im=Image.open(path).convert('RGBA'); assert im.size==(W,H),im.size
    px=im.load(); opaque={}
    for y in range(H):
        for x in range(W):
            r,g,b,a=px[x,y]
            if a>=128 and (r,g,b)!=(255,0,255): opaque[(x,y)]=(r&0xF8,g&0xF8,b&0xF8)
    cols=sorted(set(opaque.values()))
    if len(cols)>15:
        rgb=Image.new('RGB',(W,H)); q=rgb.load()
        for (x,y),c in opaque.items(): q[x,y]=c
        qi=rgb.quantize(15,dither=Image.Dither.NONE); pal=qi.getpalette(); qp=qi.load()
        opaque={k:tuple(v&0xF8 for v in pal[3*qp[k]:3*qp[k]+3]) for k in opaque}
        cols=sorted(set(opaque.values()))
    idx={c:i+1 for i,c in enumerate(cols)}
    img=[[0]*W for _ in range(H)]
    for (x,y),c in opaque.items(): img[y][x]=idx[c]
    return img,{i:c for c,i in idx.items()}
def apply(rom,orig):
    import os
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==0xC000
    if os.path.exists(CUSTOM):
        L,PAL=load_png(CUSTOM)
    else:
        import logo_art
        L=logo_art.make(logo_art.P); PAL=dict(logo_art.PAL)
    assert len(L)==H and len(L[0])==W
    lum=lambda c:c[0]*3+c[1]*6+c[2]
    used=[i for i in PAL if 1<=i<=15]
    hi=max(used,key=lambda i:lum(PAL[i])); lo_=min(used,key=lambda i:lum(PAL[i]))
    for i in range(1,16):
        c=snes(PAL.get(i,(0,0,0))); rom[PAL_ROM+2*i]=c&255; rom[PAL_ROM+2*i+1]=c>>8
    for t,x in ((0,0),(4,32),(8,64),(0xC,96),(0x100,128),(0x104,160)): blit(d,L,t,x,0,4)
    for i,t in enumerate((0x40,0x42,0x44,0x46,0x48,0x4A,0x4C,0x4E,0x140,0x142,0x144,0x146)): blit(d,L,t,16*i,32,2)
    S=start_image()
    if os.path.exists(CUSTOM): S=[[{9:hi,14:lo_}.get(v,v) for v in row] for row in S]   # START uses the logo's lightest/darkest colours
    for i,t in enumerate((0x160,0x162,0x164,0x166)): blit(d,S,t,16*i,0,2)
    blob=compress_literal(bytes(d))
    o=lo(*DST); assert len(blob)<=0x10000; rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,0xE5,0xEF,0x85,0x3E,0xA9,0x1E,0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    return L,S
