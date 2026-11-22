"""Title screen: the logo becomes the tester's "Super Legend of The Sea King" mock-up and はじめる becomes START.

The title graphics block (LZSS $8F:964F, 0xC000 bytes, loaded at $81:8102 to VRAM word $2000) also holds the
sprite tiles (block offset $8000 + tile*32, 4bpp, OBJ name table 0). はじめる is four 16x16 sprites, left to
right tiles A0, C0, E0, E2, drawn in colour 1 only.
The title sprites are metasprites listed at $81:852F (10 pointers; each = count, then 8-byte entries
y, x, tile (9 bits), attribute, size 0 = 16x16 / 2 = 32x32). Entry 0 is the logo (21 sprites, OBJ palette 0).
The new logo is the mock-up scaled to fit over the sea (x 64-239), quantised to OBJ palette 0 (ROM 0x36A38,
$86:EA38; colour 1 stays white for START), cut into 16x16 cells, and each cell with ink gets one of the
table-0 tile blocks no other title sprite uses (the old logo's 180 tiles). The new
metasprite list goes in free space at $81:FC20.
The loader writes VRAM directly, so the rebuilt block goes in bank $B5 (see labels.py)."""
import struct
import paths as P
from PIL import Image, ImageFont, ImageDraw
from lzss import decompress, compress, lo
SRC=(0x8F,0x964F); DST=(0xB5,0x9000); SITE=0x8102
FONT=P.font('DejaVuSans-Bold.ttf')
START_TILES=(0xA0,0xC0,0xE0,0xE2)
MOCKUP=P.data('logo_mockup.png')
META_PTRS=0x852F; META_N=10; META_NEW=0xFC20     # bank $81
PAL=0x36A38                                       # OBJ palette 0 in ROM
AREA=(64,18,176)
KEEP={0x0E,0x0F,0x1E,0x1F,0x28,0x29,0x38,0x39}  # the START cursor (set from code, not a metasprite) and a white bar                                  # x, y, width of the logo on screen

def mask_text(text,size,stretch=1.0):
    f=ImageFont.truetype(FONT,size); bb=f.getbbox(text)
    im=Image.new('1',(bb[2]-bb[0]+4,bb[3]-bb[1]+4),0)
    ImageDraw.Draw(im).text((2-bb[0],2-bb[1]),text,font=f,fill=1)
    if stretch!=1.0: im=im.resize((int(im.size[0]*stretch),im.size[1]),Image.NEAREST)
    return im.crop(im.getbbox())

def start_image():
    w,h=64,16; img=[[0]*w for _ in range(h)]
    m=mask_text('START',12,1.15); px=m.load()
    x0=(w-m.size[0])//2; y0=(h-m.size[1])//2
    assert m.size[0]<=w and m.size[1]<=h
    for y in range(m.size[1]):
        for x in range(m.size[0]):
            if px[x,y]: img[y0+y][x0+x]=1
    return img

def metasprites(rom):
    out=[]
    for p in struct.unpack_from('<%dH'%META_N,rom,META_PTRS):
        o=lo(0x81,p); n=struct.unpack_from('<H',rom,o)[0]
        out.append((p,[struct.unpack_from('<hhHBB',rom,o+2+8*k) for k in range(n)]))
    return out
def cells_of(t,sz):
    s=4 if sz&2 else 2
    return {(t&0x100)|((((t>>4)+dy)&0xF)<<4)|((t+dx)&0xF) for dy in range(s) for dx in range(s)}
def free_blocks(orig):
    """16x16 tile blocks (t, t+1, t+16, t+17) in name table 0 that only the logo uses."""
    ms=metasprites(orig); other=set(); logo=set()
    for i,(p,ents) in enumerate(ms):
        for y,x,t,a,sz in ents: (logo if i==0 else other).update(cells_of(t,sz))
    free=[t for t in range(256) if t not in other and t not in KEEP]
    blocks=[]; taken=set()
    for t in free:
        b={t,t+1,t+16,t+17}
        if t%16<15 and t<0xF0 and b<=set(free) and not b&taken: blocks.append(t); taken|=b
    return blocks,logo|(set(free)-other)

def logo_image():
    """The mock-up scaled to the logo area: (width, height, rgb pixels, opaque mask)."""
    im=Image.open(MOCKUP).convert('RGB'); px=im.load(); W0,H0=im.size
    bg=px[10,10]
    m=Image.new('L',im.size,0); mp=m.load()
    for y in range(H0):
        for x in range(W0):
            c=px[x,y]
            if abs(c[0]-bg[0])+abs(c[1]-bg[1])+abs(c[2]-bg[2])>60: mp[x,y]=255
    box=m.getbbox(); im=im.crop(box); m=m.crop(box)
    w=AREA[2]; h=round(w*im.size[1]/im.size[0])
    return w,h,im.resize((w,h),Image.LANCZOS),m.resize((w,h),Image.BOX)

def quantise(rgb,mask):
    """Colour indices (0 = transparent, 1 = white) and the 15 BGR555 colours for indices 1-15."""
    w,h=rgb.size; op=[(x,y) for y in range(h) for x in range(w) if mask.getpixel((x,y))>=128]
    sample=Image.new('RGB',(len(op),1)); sample.putdata([rgb.getpixel(p) for p in op])
    q=sample.quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    pal=q.getpalette()[:45]; cols=[tuple(pal[3*i:3*i+3]) for i in range(15)]
    white=max(range(15),key=lambda i:sum(cols[i]))
    order=[white]+[i for i in range(15) if i!=white]          # palette slot k+1 = cols[order[k]]
    slot={c:k+1 for k,c in enumerate(order)}
    idx=[[0]*w for _ in range(h)]
    for (x,y),v in zip(op,q.get_flattened_data() if hasattr(q,"get_flattened_data") else q.getdata()): idx[y][x]=slot[v]
    bgr=[(c[2]>>3)<<10|(c[1]>>3)<<5|(c[0]>>3) for c in (cols[i] for i in order)]
    return idx,bgr

def put_tile(d,n,pix):
    o=0x8000+n*32
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            v=pix[y][x]
            for k in range(4): p[k]|=((v>>k)&1)<<(7-x)
        d[o+2*y]=p[0]; d[o+2*y+1]=p[1]; d[o+16+2*y]=p[2]; d[o+17+2*y]=p[3]

def apply(rom,orig):
    d=bytearray(decompress(orig,lo(*SRC))[0]); assert len(d)==0xC000
    blocks,clear=free_blocks(orig)
    for t in clear: put_tile(d,t,[[0]*8 for _ in range(8)])
    w,h,rgb,mask=logo_image(); idx,bgr=quantise(rgb,mask)
    x0,y0=AREA[0],AREA[1]; ents=[]
    for cy in range(0,h,16):
        for cx in range(0,w,16):
            cell=[[idx[cy+y][cx+x] if cy+y<h and cx+x<w else 0 for x in range(16)] for y in range(16)]
            if not any(any(r) for r in cell): continue
            assert blocks,'out of sprite tiles'
            t=blocks.pop(0)
            for ty in (0,1):
                for tx in (0,1): put_tile(d,t+ty*16+tx,[r[tx*8:tx*8+8] for r in cell[ty*8:ty*8+8]])
            ents.append((y0+cy,x0+cx,t,0x20,0))
    S=start_image()
    for i,t in enumerate(START_TILES):
        for ty in range(2):
            for tx in range(2):
                put_tile(d,t+ty*16+tx,[[S[ty*8+y][16*i+tx*8+x] for x in range(8)] for y in range(8)])
    blob=compress(bytes(d)); o=lo(*DST)
    assert DST[1]+len(blob)<=0x10000 and set(orig[o:o+len(blob)])<={0} and set(rom[o:o+len(blob)])<={0}
    rom[o:o+len(blob)]=blob
    assert orig[SITE:SITE+10]==bytes([0xA9,SRC[1]&255,SRC[1]>>8,0x85,0x3E,0xA9,SRC[0],0x00,0x85,0x40])
    rom[SITE+1:SITE+3]=bytes([DST[1]&255,DST[1]>>8]); rom[SITE+6]=DST[0]
    # metasprite list and pointer
    tbl=struct.pack('<H',len(ents))+b''.join(struct.pack('<hhHBB',*e) for e in ents)
    o=lo(0x81,META_NEW); assert set(orig[o-16:o+len(tbl)])<={0} or set(orig[o-16:o+len(tbl)])<={0xFF},'bank $81 space'
    assert rom[o:o+len(tbl)]==orig[o:o+len(tbl)]
    rom[o:o+len(tbl)]=tbl; struct.pack_into('<H',rom,META_PTRS,META_NEW)
    # OBJ palette 0, colours 1-15
    for k,c in enumerate(bgr): struct.pack_into('<H',rom,PAL+2+2*k,c)
    return len(ents),len(blob)

if __name__=='__main__':
    w,h,rgb,mask=logo_image(); idx,bgr=quantise(rgb,mask)
    cols=[(0x5a,0x28,0x28)]+[((c&31)<<3,((c>>5)&31)<<3,((c>>10)&31)<<3) for c in bgr]
    out=Image.new('RGB',(w,h))
    out.putdata([cols[idx[y][x]] if idx[y][x] else (88,160,232) for y in range(h) for x in range(w)])
    out.resize((w*4,h*4),Image.NEAREST).save(P.out('logo_preview.png'))
    print(w,h,len(free_blocks(open(P.ROM,'rb').read())[0]),'blocks')
