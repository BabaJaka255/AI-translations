"""Export every font and replaced graphic from a patched ROM into ../fonts and ../graphics
(PNG previews at 1x and 4x, plus raw/1bpp data and a JSON of the hand-drawn pixel fonts).

    python3 analysis/export_assets.py            (uses out/knt2_en.sfc from build_patch2.py)"""
import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import os, json
from PIL import Image, ImageDraw
import lzss, map_labels, item_icons, gear_placeholders, labels, name_entry, postcard, field_signs, glyph_patch, ui_font

orig=open(P.ROM,'rb').read()
rom=open(P.out('knt2_en.sfc'),'rb').read()
FD=os.path.join(P.ROOT,'gfx','fonts','made'); GD=os.path.join(P.ROOT,'gfx','sheets')
os.makedirs(FD,exist_ok=True); os.makedirs(GD,exist_ok=True)
GREY4=[(16,16,24),(60,70,110),(150,160,200),(250,250,250)]
def ramp(n): return [tuple(int(i*255/(n-1)) for _ in range(3)) for i in range(n)]
def save(img,path,scale=4):
    img.save(path); img.resize((img.size[0]*scale,img.size[1]*scale),Image.NEAREST).save(path.replace('.png','_x%d.png'%scale))
def tiles_img(d,bpp,cols,pal=None,n=None):
    n=n or len(d)//(8*bpp); rows=(n+cols-1)//cols; pal=pal or ramp(1<<bpp)
    img=Image.new('RGB',(cols*8,rows*8)); px=img.load()
    for t in range(n):
        b=t*8*bpp
        for y in range(8):
            pl=[d[b+(p//2)*16+2*y+(p%2)] for p in range(bpp)]
            for x in range(8): px[(t%cols)*8+x,(t//cols)*8+y]=pal[sum(((pl[p]>>(7-x))&1)<<p for p in range(bpp))]
    return img
def grid_px(rows_fn,w,h,cols,count,pal,pad=1):
    """rows_fn(i) -> h rows of w values; lays out glyphs in a grid with a 1px gutter."""
    R=(count+cols-1)//cols; img=Image.new('RGB',(cols*(w+pad)+pad,R*(h+pad)+pad),(90,30,30)); px=img.load()
    for i in range(count):
        g=rows_fn(i); ox=pad+(i%cols)*(w+pad); oy=pad+(i//cols)*(h+pad)
        for y in range(h):
            for x in range(w): px[ox+x,oy+y]=pal[g[y][x]]
    return img
def strip(img,label,scale=4):
    """img plus a caption underneath (already scaled)."""
    im=img.resize((img.size[0]*scale,img.size[1]*scale),Image.NEAREST)
    out=Image.new('RGB',(max(im.size[0],8*len(label)+8),im.size[1]+16),(0,0,0)); out.paste(im,(0,0))
    ImageDraw.Draw(out).text((2,im.size[1]+2),label,fill=(255,255,255)); return out
def stack(imgs,gap=6):
    W=max(i.size[0] for i in imgs); H=sum(i.size[1] for i in imgs)+gap*(len(imgs)-1)
    out=Image.new('RGB',(W,H),(0,0,0)); y=0
    for i in imgs: out.paste(i,(0,y)); y+=i.size[1]+gap
    return out
manifest={}

# 1) Dialogue font: 8x16, ASCII 0x20-0x7E, stored in the game's 16x16 glyph layout at $30:A000 (ROM 0x182000)
FONT=0x182000
def dlg(i):
    base=FONT+(i>>3)*0x100+(i&7)*0x10
    return [[(rom[base+(y if y<8 else 0x80+y-8)]>>(7-x))&1 for x in range(8)] for y in range(16)]
save(grid_px(dlg,8,16,16,95,[(20,20,30),(255,255,255)]),FD+'/dialogue_font_8x16.png')
open(FD+'/dialogue_font_8x16_1bpp.bin','wb').write(bytes(sum(dlg(i)[y][x]<<(7-x) for x in range(8)) for i in range(95) for y in range(16)))
manifest['dialogue_font_8x16']='ASCII 0x20-0x7E, 16 bytes per glyph (1bpp rows). Source: X11 koi8x16 bitmap font (build/fonts/koi8x16.pcf). In-game: ROM 0x182000 ($30:A000), 16x16 slot layout, left half used.'

# 2) Keyboard glyph blocks (16x16 cells, staging layout)
def blockimg(o,size):
    d=rom[o:o+size]; img=Image.new('RGB',(128,size//0x200*16)); px=img.load()
    for line in range(size//0x200):
        for k in range(8):
            for half in (0,1):
                for t in (0,1):
                    b=line*0x200+half*0x100+k*0x20+t*0x10
                    for y in range(8):
                        p0,p1=d[b+2*y],d[b+2*y+1]
                        for x in range(8):
                            v=((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1)
                            px[k*16+t*8+x,line*16+half*8+y]=GREY4[v]
    return img
NE=name_entry.BASE
kb=[strip(blockimg(NE,0xC00),'name entry: cells 0-47'),strip(blockimg(NE+0xC00,0x1000),'name entry: cells 48-109')]
for m,a in enumerate(postcard.BLK): kb.append(strip(blockimg(name_entry.lo(0x38,a),0xE00),'postcard mode %d'%m))
stack(kb).save(GD+'/keyboards.png')
manifest['keyboards']='Pre-rendered 16x16 keyboard cells (name entry, postcard UPPER/lower/symbols), 2bpp staging layout, bank $38.'

# 3) Map label font: 8x8, outlined, transparent background (LZSS at $3B:8000)
d,_=lzss.decompress(rom,lzss.lo(0x3B,0x8000))
mpal=[(0,120,170),(20,20,30),(255,255,255),(255,255,255)]
save(tiles_img(d,2,16,mpal),FD+'/map_label_font_8x8.png')
open(FD+'/map_label_font_8x8_2bpp.bin','wb').write(d)
slots=[s for s in range(80) if s not in map_labels.KEEP and s!=78]
manifest['map_label_font_8x8']={'note':'2bpp SNES tiles, colour 3 = letter, 1 = outline, 0 = transparent. Derived from X11 koi5x8. Slot -> character:',
    'slots':{**{str(s):ch for ch,s in zip(map_labels.CHARS,slots)},'78':'-','77':'(marker, original)'}}

# 4) Hand-drawn pixel fonts
pix={'tiny_3x5 (item icons; M is 5 wide, N 4 wide)':item_icons.FONT,'small_5x5 (gear slots)':gear_placeholders.F5,
     'small_5x4 (gear slots, tight)':gear_placeholders.F4,'plaque_art_12x12 (town signs)':field_signs.ART,
     'yen_16x16 (main font counter glyph)':{'yen':glyph_patch.YEN},'yen_8x16 (window UI font)':{'yen':ui_font.YEN}}
json.dump(pix,open(FD+'/pixel_fonts.json','w'),indent=1)
imgs=[]
for name,f in pix.items():
    ks=list(f); w=max(len(r) for k in ks for r in f[k]); h=max(len(f[k]) for k in ks)
    def g(i,f=f,ks=ks,w=w,h=h):
        rows=f[ks[i]]; return [[1 if y<len(rows) and x<len(rows[y]) and rows[y][x]=='#' else 0 for x in range(w)] for y in range(h)]
    imgs.append(strip(grid_px(g,w,h,min(16,len(ks)),len(ks),[(20,20,30),(255,255,255)]),name+': '+''.join(k if len(k)==1 else '['+k+']' for k in ks)[:60]))
stack(imgs).save(FD+'/pixel_fonts.png')

# 5) Menu label art (bank 7, 2bpp): before / after
def label_rows(src,lo_,hi,rw):
    return tiles_img(bytes(src[lo_:hi]),2,rw,GREY4)
def label_sheet(src):
    # 12-tile rows (0x180 bytes = 12 top tiles then 12 bottom tiles) and 16-tile rows (0x200 bytes)
    return label_rows(src,0x38000,0x3A400,12),label_rows(src,0x3A400,0x3B300,16)
for tag,src in (('original',orig),('english',rom)):
    a,b=label_sheet(src)
    save(stack([a,b]),GD+'/menu_labels_%s.png'%tag,3)
manifest['menu_labels']='Bank 7 label art (ROM 0x38000-0x3B2FF), 2bpp. Each 16px label row is stored as a run of top-half tiles followed by bottom-half tiles.'

# 6) Window UI font ($30:C000 literal LZSS) before / after
for tag,src,at in (('original',orig,lzss.lo(0x0C,0xF800)),('english',rom,lzss.lo(0x30,0xC000))):
    d,_=lzss.decompress(src,at); save(tiles_img(d,2,16,GREY4),GD+'/window_ui_font_%s.png'%tag,3)

# 7) Raw 4bpp sprite cells: item icons and gear placeholders
def cell(src,base,tr,tc,w,h):
    img=Image.new('RGB',(w*8,h*8)); pal=ramp(16)
    for r in range(h):
        for c in range(w):
            img.paste(tiles_img(bytes(src[base+(tr+r)*0x200+(tc+c)*32:][:32]),4,1,pal),(c*8,r*8))
    return img
cells=[]
for text,(tr,tc) in item_icons.CELLS.items():
    cells+= [strip(cell(orig,item_icons.B,tr,tc,4,2),text+' before'),strip(cell(rom,item_icons.B,tr,tc,4,2),text+' after')]
for base,tr,tc,w,h,text,v in gear_placeholders.SLOTS:
    cells+= [strip(cell(orig,base,tr,tc,w,h),text+' before'),strip(cell(rom,base,tr,tc,w,h),text+' after')]
stack(cells,4).save(GD+'/sprite_cells_before_after.png')

# 8) Field tilesets (signs, plaques, banner): full sheets after patching
for i,t in enumerate(field_signs.TABLE):
    a=rom[t]|rom[t+1]<<8; bk=rom[t+2]
    d,_=lzss.decompress(rom,lzss.lo(bk,a)); save(tiles_img(d,4,32,ramp(16)),GD+'/field_tileset_%d_%02X%04X.png'%(i,bk,a),2)

# 9) Title logo
from PIL import Image as I
I.open(P.b('logo_custom.png')).save(GD+'/title_logo_192x48.png')
json.dump(manifest,open(FD+'/fonts_manifest.json','w'),indent=1)
print('exported to',FD,'and',GD)
