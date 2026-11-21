"""English replacements for the pre-rendered menu label art in ROM bank 7 (0x38000-0x3B2FF, 2bpp, bg=1, ink=3).
Rows are 12 tiles wide (0x38000-0x3A3FF, 0x180 bytes per 16px line) or 16 tiles wide (0x3A400+, 0x200 bytes)."""
import paths as P
from PIL import PcfFontFile, Image
pcf=PcfFontFile.PcfFontFile(open(P.font('koi8x16.pcf'),'rb'))
def glyph(ch):
    im=pcf.glyph[ord(ch)][3].convert('1'); px=im.load()
    on={(x,y) for x in range(8) for y in range(16) if px[x,y]}
    if ch in 'il':   # narrow forms for labels: drop the foot serif
        foot=max(y for x,y in on); on={(x,y) for x,y in on if y!=foot or x==4}
    cols=sorted({x for x,y in on})
    if not cols: return 2,[]          # space
    x0,x1=min(cols),max(cols)
    return x1-x0+1,[(x-x0,y) for x,y in on]
def render(text,w,gap=1,align='c'):
    """Place glyphs left to right; with gap=0 add a 1px gap only where two glyphs would touch."""
    gl=[glyph(c) for c in text]
    xs=[];x=0;prev=None
    for gw,pts in gl:
        if prev is not None:
            pw,ppts,px0=prev
            g=gap
            if g==0:
                right={y for (xx,y) in ppts if xx==pw-1}
                left={y for (xx,y) in pts if xx==0}
                if any(y in right or y-1 in right or y+1 in right for y in left): g=1
            x+=g
        xs.append(x); prev=(gw,pts,x); x+=gw
    tw=x
    if tw>w: return None
    img=[[1]*w for _ in range(16)]
    off={'c':(w-tw)//2,'l':0,'r':w-tw-1}[align] if tw<w else 0
    for (gw,pts),x0 in zip(gl,xs):
        for px_,py in pts: img[py][off+x0+px_]=3
    return img
# (rom row address, row width in tiles, start col, width in cols, English)
L12,L16=12,16
LABELS=[
 (0x38000,L12,0,6,'Stream'),(0x38000,L12,6,6,'Alpine'),
 (0x38180,L12,0,6,'Creek'),(0x38180,L12,6,6,'Lake'),
 (0x38300,L12,0,6,'Plains'),(0x38300,L12,6,6,'Coast'),
 (0x38480,L12,0,6,'Bait'),(0x38480,L12,6,6,'Gear'),
 (0x38600,L12,0,6,'Food'),(0x38600,L12,6,6,'Items'),
 (0x38780,L12,0,6,'5 Fish'),(0x38780,L12,6,6,'10 Fish'),
 (0x38900,L12,0,6,'20 Fish'),(0x38900,L12,6,6,'30 Fish'),
 (0x38a80,L12,0,6,'Rods'),(0x38a80,L12,6,6,'Lures'),
 (0x38c00,L12,0,6,'Flies'),(0x38c00,L12,6,6,'Tackle'),
 (0x38d80,L12,0,6,'Sinkers'),(0x38d80,L12,6,6,'Hooks'),
 (0x38f00,L12,0,6,'Spin Rod'),(0x38f00,L12,6,6,'Fly Rod'),
 (0x39080,L12,0,6,'Home'),(0x39080,L12,6,6,'Sell'),
 (0x39200,L12,0,6,'Give'),(0x39200,L12,6,6,'Price'),
 (0x39380,L12,0,6,'Body'),(0x39380,L12,6,6,'Wing'),
 (0x39500,L12,0,6,'Tail'),
 (0x39680,L12,0,4,'Fish'),(0x39680,L12,4,4,'Bait'),(0x39680,L12,8,4,'Gear'),
 (0x39800,L12,0,4,'Eat'),(0x39800,L12,4,4,'Item'),(0x39800,L12,8,4,'Creel'),
 (0x39980,L12,0,4,'Move'),(0x39980,L12,4,4,'Flies'),(0x39980,L12,8,4,'Lure'),
 (0x39b00,L12,0,4,'Buy'),(0x39b00,L12,4,4,'Sell'),(0x39b00,L12,8,4,'Rods'),
 (0x39c80,L12,0,4,'Fight'),(0x39c80,L12,6,6,'Feed'),
 (0x39e00,L12,0,6,'Run'),(0x39e00,L12,6,6,'Yes'),
 (0x39f80,L12,0,6,'No'),
 (0x3a100,L12,0,6,'Float'),(0x3a100,L12,6,6,'Casting'),
 (0x3a280,L12,0,6,'Lure'),(0x3a280,L12,6,6,'Fly'),
 (0x3a400,L16,0,8,'Mayfly'),(0x3a400,L16,8,8,'Caddis'),
 (0x3a600,L16,0,8,'Diptera'),(0x3a600,L16,8,8,'Stonefly'),
 (0x3a800,L16,0,8,'Terrestr.'),(0x3a800,L16,8,4,'Total'),
 # name entry: box title / start of the prompt (the same tiles are used for both), buttons
 (0x3ac00,L16,0,4,''),(0x3ac00,L16,4,4,'Name','r'),
 (0x3ae00,L16,0,16,' your character!','l'),
 (0x3aa00,L16,6,4,'Done'),
 (0x3aa00,L16,2,2,''),                          # postcard honorific (sama)
 # postcard keyboard: mode button shows the mode it switches to; fixed keys
 (0x3b000,L16,0,4,'abc'),(0x3b200,L16,4,4,'Sym'),(0x3b200,L16,0,4,'ABC'),
 (0x3b000,L16,4,2,'-'),(0x3b000,L16,8,4,'Line'),(0x3b000,L16,12,2,','),(0x3b000,L16,14,2,'.'),
]
def tile_addr(row,rw,col,half): return row+half*rw*16+col*16
def read_px(rom,row,rw,c0,w):
    img=[[0]*(w*8) for _ in range(16)]
    for c in range(w):
        for half in range(2):
            b=tile_addr(row,rw,c0+c,half)
            for y in range(8):
                p0,p1=rom[b+2*y],rom[b+2*y+1]
                for x in range(8): img[half*8+y][c*8+x]=((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1)
    return img
def write_px(rom,row,rw,c0,w,img):
    for c in range(w):
        for half in range(2):
            b=tile_addr(row,rw,c0+c,half)
            for y in range(8):
                p0=p1=0
                for x in range(8):
                    v=img[half*8+y][c*8+x]; p0|=(v&1)<<(7-x); p1|=(v>>1)<<(7-x)
                rom[b+2*y]=p0; rom[b+2*y+1]=p1
def apply(rom):
    bad=[]
    for row,rw,c0,w,text,*al in LABELS:
        old=read_px(rom,row,rw,c0,w)
        img=None
        for gap in (1,0):
            img=render(text,w*8,gap,*al)
            if img: break
        if img is None: bad.append(text); continue
        for y in range(16):     # keep full-width rule lines that belong to the frame
            if all(v==3 for v in old[y]): img[y]=old[y]
        write_px(rom,row,rw,c0,w,img)
    return bad
