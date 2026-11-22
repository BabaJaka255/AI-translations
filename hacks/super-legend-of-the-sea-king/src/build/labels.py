"""English replacements for pre-rendered label art.

1. Menu label art, uncompressed 2bpp at ROM 0x48000-0x4BBFF ($89:8000-), bg 1 / ink 3. The same layout as
   Kawa no Nushi Tsuri 2: rows of 12 tiles (0x180 bytes, 12 top tiles then 12 bottom) up to 0x4A3FF,
   then rows of 16 tiles (0x200 bytes).
2. The window UI font, LZSS $90:9A71 (status labels, はい/いいえ, digits) and its larger variant $89:BBFF
   (adds place names and the name prompt). Both are rebuilt and stored as literal-only LZSS in expanded ROM,
   and their loaders are repointed."""
import paths as P
from PIL import PcfFontFile
from lzss import decompress, compress, lo
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
            pw,ppts=prev; g=gap
            if g==0:
                right={y for (xx,y) in ppts if xx==pw-1}
                left={y for (xx,y) in pts if xx==0}
                if any(y in right or y-1 in right or y+1 in right for y in left): g=1
            x+=g
        xs.append(x); prev=(gw,pts); x+=gw
    tw=x
    if tw>w: return None
    img=[[1]*w for _ in range(16)]
    off={'c':(w-tw)//2,'l':0,'r':w-tw-1}[align] if tw<w else 0
    for (gw,pts),x0 in zip(gl,xs):
        for px_,py in pts: img[py][off+x0+px_]=3
    return img
def fit(texts,w,align='c'):
    """First candidate that fits, trying normal spacing before tight spacing."""
    for t in (texts if isinstance(texts,tuple) else (texts,)):
        for gap in (1,0):
            img=render(t,w,gap,align)
            if img: return img
    return None

# (row address, row width in tiles, start col, width in cols, English or candidates, [align])
L12,L16=12,16
LABELS=[
 (0x48000,L12,0,6,('Breakwater','Jetty')),(0x48000,L12,6,6,'Beach'),
 (0x48180,L12,0,6,'Rocks'),(0x48180,L12,6,6,'Coast'),
 (0x48300,L12,0,6,'Islet'),(0x48300,L12,6,6,('Open Sea','Ocean')),
 (0x48480,L12,0,6,('Far Isle','Isle')),(0x48480,L12,6,6,'Home'),
 (0x48600,L12,0,6,('Command','Cmd')),(0x48600,L12,6,6,'Inn'),
 (0x48780,L12,0,6,'Tackle'),(0x48780,L12,6,6,('Fish Shop','Fishmart','Market')),
 (0x48900,L12,0,6,'Give'),
 (0x48a80,L12,0,6,'Float'),(0x48a80,L12,6,6,('Live Bait','Live')),
 (0x48c00,L12,0,6,'Lure'),(0x48c00,L12,6,6,'Night'),
 (0x48d80,L12,0,6,('Cast-in','Cast')),(0x48d80,L12,6,6,('Tightline','Tight')),
 (0x48f00,L12,0,6,('Feeder','Bishi')),(0x48f00,L12,6,6,'Wall'),
 (0x49080,L12,0,6,'Sabiki'),(0x49080,L12,6,6,'Cage'),
 (0x49200,L12,0,6,'Surf'),(0x49200,L12,6,6,('Feeder','Bishi')),
 (0x49380,L12,0,6,'Squid'),(0x49380,L12,6,6,'Octopus'),
 (0x49500,L12,0,6,'Boat'),(0x49500,L12,6,6,'Trolling'),
 (0x49680,L12,0,6,'Cave'),
 (0x49800,L12,0,6,'Bait'),(0x49800,L12,6,6,'Lure'),
 (0x49980,L12,0,6,('Decoy Hook','Decoy')),(0x49980,L12,6,6,'Rod'),
 (0x49b00,L12,0,6,'Sinker'),(0x49b00,L12,6,6,'Cage'),
 (0x49c80,L12,0,6,'Hook'),(0x49c80,L12,6,6,'Float'),
 (0x49e00,L12,0,6,'Rig'),(0x49e00,L12,6,6,('Boat Rod','B. Rod')),
 (0x49f80,L12,0,6,'Food'),(0x49f80,L12,6,6,'Items'),
 (0x4a100,L12,0,6,('Holds 10','Cap 10')),(0x4a100,L12,6,6,('Holds 20','Cap 20')),
 (0x4a280,L12,0,6,('Holds 40','Cap 40')),(0x4a280,L12,6,6,'Price'),
 (0x4a400,L16,0,4,'Fish'),(0x4a400,L16,4,4,'Bait'),(0x4a400,L16,8,4,'Gear'),(0x4a400,L16,12,4,'Eat'),
 (0x4a600,L16,0,4,'Item'),(0x4a600,L16,4,4,'Creel'),(0x4a600,L16,8,4,'Move'),(0x4a600,L16,12,4,'Lure'),
 (0x4a800,L16,0,4,'Rod'),(0x4a800,L16,4,4,'Lead'),(0x4a800,L16,8,4,'Hook'),(0x4a800,L16,12,4,'Float'),
 (0x4aa00,L16,0,4,'Cage'),(0x4aa00,L16,4,4,'Rig'),(0x4aa00,L16,12,4,('Decoy','Fly')),
 (0x4ac00,L16,0,4,'Bait'),(0x4ac00,L16,4,4,'Lure'),(0x4ac00,L16,8,4,('Decoy','Fly')),(0x4ac00,L16,12,4,'Item'),
 (0x4ae00,L16,0,4,('Lunch','Meal')),(0x4ae00,L16,8,4,'Net'),(0x4ae00,L16,12,4,('Cooler','Ice','Box')),
 (0x4b000,L16,0,4,'Fight'),(0x4b000,L16,4,4,'Eat'),(0x4b000,L16,8,4,'Feed'),(0x4b000,L16,12,4,'Run'),
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
def keep_rules(old,img):
    for y in range(16):     # keep full-width rule lines that belong to the frame
        if all(v==3 for v in old[y]): img[y]=old[y]
    return img
def apply_art(rom):
    bad=[]
    for row,rw,c0,w,text,*al in LABELS:
        img=fit(text,w*8,*al)
        if img is None: bad.append(text); continue
        write_px(rom,row,rw,c0,w,keep_rules(read_px(rom,row,rw,c0,w),img))
    return bad

# --- UI font blocks: tile t (top) and t+0x10 (bottom), 16 tiles per row ---
# The loader ($80:92C6) sets the data bank to the source bank and writes $2118 with absolute addressing, so the
# source must sit in a bank with the I/O mirror ($80-$BF), i.e. in the original 2 MB. Bank $B5 is unused
# (zero-filled) and holds these blocks and the title block.
UI_BLOCKS={  # (bank, addr) -> (new bank, new addr, loader ROM offsets)
 (0x90,0x9A71):(0xB5,0x8000,[0x10024]),
 (0x89,0xBBFF):(0xB5,0x8500,[0x8a5a,0x8ec5,0x978a,0xabab,0xbe8c,0xc7a4,0xd3e7]),
}
COMMON=[(0x48,4,'HP'),(0x4C,4,'Yen'),(0x6C,4,('Kinds','Spp.')),(0x8C,4,'Total'),
        (0xCA,4,'Yes'),(0xCE,2,'No')]
EXTRA={(0x89,0xBBFF):[(0x60,6,('Breakwater','Jetty')),(0x66,6,'Beach'),(0x80,6,'Rocks'),(0x86,6,'Coast'),
                      # the name box title reuses 名前 (A0-A3) from the prompt, so the prompt starts with that word
                      (0xA0,4,'Name','r'),(0xA4,12,(' your angler.',' it, please.'),'l'),(0xC0,4,'')]}
def blk_get(d,t,n):
    img=[[0]*(n*8) for _ in range(16)]
    for c in range(n):
        for half in (0,1):
            b=(t+c+half*0x10)*16
            for y in range(8):
                p0,p1=d[b+2*y],d[b+2*y+1]
                for x in range(8): img[half*8+y][c*8+x]=((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1)
    return img
def blk_put(d,t,img):
    for c in range(len(img[0])//8):
        for half in (0,1):
            b=(t+c+half*0x10)*16
            for y in range(8):
                p0=p1=0
                for x in range(8):
                    v=img[half*8+y][c*8+x]; p0|=(v&1)<<(7-x); p1|=(v>>1)<<(7-x)
                d[b+2*y]=p0; d[b+2*y+1]=p1
YEN=["........","........","........","........",".#...#..",".#...#..","..#.#...","...#....",".#####..","...#....",".#####..","...#....","...#....","...#....","........","........"]
COMMA=["........","........","........","........","...##...","...##...","....#...","...#...."]
STOP=["........","........","........","........","........","...##...","...##...","........"]
def apply_ui(rom,orig):
    bad=[]
    for (sb,sa),(nb,na,loaders) in UI_BLOCKS.items():
        d=bytearray(decompress(orig,lo(sb,sa))[0])
        for t,n,text,*al in COMMON+EXTRA.get((sb,sa),[]):
            img=fit(text,n*8,*al) if text else [[1]*(n*8) for _ in range(16)]
            if img is None: bad.append(text); continue
            blk_put(d,t,keep_rules(blk_get(d,t,n),img))
        blk_put(d,0x0C,[[3 if ch=='#' else 1 for ch in r] for r in YEN])   # 円 -> ¥
        blk_put(d,0x0F,[[1]*8 for _ in range(16)])                          # 尾 (fish counter) -> blank
        if (sb,sa)==(0x89,0xBBFF):     # board keyboard marks (single 8x8 tiles): 、 -> comma, 。 -> full stop, ゛ ゜ -> blank
            for t,art in ((0x2A,COMMA),(0x3A,STOP),(0x21,['.'*8]*8),(0x31,['.'*8]*8)):
                for y,r in enumerate(art):
                    d[t*16+2*y]=0xFF; d[t*16+2*y+1]=sum(0x80>>x for x,ch in enumerate(r) if ch=='#')
        blob=compress(bytes(d)); o=lo(nb,na)
        assert na+len(blob)<=0x10000 and set(orig[o:o+len(blob)])<={0} and set(rom[o:o+len(blob)])<={0},(hex(nb),hex(na))
        rom[o:o+len(blob)]=blob
        for a in loaders:
            assert orig[a:a+10]==bytes([0xA9,sa&255,sa>>8,0x85,0x3E,0xA9,sb,0x00,0x85,0x40]),hex(a)
            rom[a+1]=na&255; rom[a+2]=na>>8; rom[a+6]=nb
    # yes/no window template ($82:C70F): はい = CA-CD, いいえ = CC CD CC CD CE CF. "No" now lives in CE-CF alone.
    for top in (0xCC,0xDC):
        old=b''.join(bytes([t,0x3D]) for t in (top,top+1,top,top+1,top+2,top+3))
        new=b''.join(bytes([t,0x3D]) for t in (top+2,top+3,0,0,0,0))
        o=orig.find(old,0x14700,0x14760); assert o>0,hex(top); rom[o:o+12]=new
    return bad
def apply(rom,orig):
    return apply_art(rom)+apply_ui(rom,orig)
