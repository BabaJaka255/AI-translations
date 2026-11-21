"""Town building plaques (宿 inn, 魚 fish shop, 釣 tackle shop). Each of the six area tilesets
(table at ROM $074E) holds the three plaques as 2x2 tiles inside a carved frame. We redraw the 12x12
interior: INN as text, a fish and a fishing hook as pictures. Tilesets are recompressed with real LZSS."""
import struct
from lzss import decompress, compress, lo
TABLE=[0x74E,0x756,0x75E,0x766,0x76E,0x776]
DST_BANK=0x3B; DST_START=0x8800
REF=(0x21,0xFAF7)
REF_PLAQUES={'inn':(0x21E,0x21F,0x22C,0x22D),'fish':(0x220,0x221,0x22E,0x22F),'tackle':(0x222,0x223,0x230,0x231)}
# 12x12 interior art, '#' = ink
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
INK,SHADE,BG=5,3,1   # colour indices in the reference tileset
def tiles_of(d):
    return [[[sum(((d[t*32+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)] for t in range(len(d)//32)]
def put_tile(d,t,pix):
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            v=pix[y][x]
            for k in range(4): p[k]|=((v>>k)&1)<<(7-x)
        d[t*32+2*y]=p[0]; d[t*32+2*y+1]=p[1]; d[t*32+16+2*y]=p[2]; d[t*32+17+2*y]=p[3]
def quad(T,q):
    a,b,c,e=q; img=[[0]*16 for _ in range(16)]
    for (t,ox,oy) in ((a,0,0),(b,8,0),(c,0,8),(e,8,8)):
        for y in range(8):
            for x in range(8): img[oy+y][ox+x]=T[t][y][x]
    return img
def design(ref_img,name):
    img=[row[:] for row in ref_img]
    art=ART[name]
    for y in range(12):
        for x in range(12): img[2+y][2+x]=BG
    for y in range(12):
        for x in range(12):
            if art[y][x]=='#':
                img[2+y][2+x]=INK
                if y+1<12 and x+1<12 and art[y+1][x+1]!='#' and img[3+y][3+x]==BG: img[3+y][3+x]=SHADE
    return img
def canon(seq):
    m={}; return tuple(m.setdefault(v,len(m)) for v in seq)
def edge_sig(t,part):
    if part=='TL': px=[t[0][i] for i in range(8)]+[t[1][i] for i in range(8)]+[t[y][0] for y in range(8)]
    if part=='BL': px=[t[6][i] for i in range(8)]+[t[7][i] for i in range(8)]+[t[y][0] for y in range(8)]
    return canon(px)
REF_SIG={}
def find_quads(T):
    """locate the three plaques in a tileset by matching the reference frame (canonical)."""
    out={}
    return out
def apply(rom,orig):
    d0=decompress(orig,lo(*REF))[0]; T0=tiles_of(d0)
    new={n:design(quad(T0,q),n) for n,q in REF_PLAQUES.items()}
    ref_imgs={n:quad(T0,q) for n,q in REF_PLAQUES.items()}
    REF_SIG['TL']=edge_sig(T0[0x21E],'TL'); REF_SIG['BL']=edge_sig(T0[0x22C],'BL')
    pos=lo(DST_BANK,DST_START); report=[]
    for ent in TABLE:
        a,b=struct.unpack('<HH',orig[ent:ent+4])
        d=bytearray(decompress(orig,lo(b,a))[0]); T=tiles_of(d)
        done=0
        tl=[i for i,t in enumerate(T) if edge_sig(t,'TL')==REF_SIG['TL']]
        bl=[i for i,t in enumerate(T) if edge_sig(t,'BL')==REF_SIG['BL']]
        assert len(tl)==3 and len(bl)==3,(hex(a),tl,bl)
        w=bl[0]-tl[0]
        for n,t in zip(('inn','fish','tackle'),tl):
            R=ref_imgs[n]; Q=quad(T,(t,t+1,t+w,t+w+1))
            from collections import Counter
            cm={}
            for y in range(16):
                for x in range(16): cm.setdefault(R[y][x],Counter())[Q[y][x]]+=1
            m={r:c.most_common(1)[0][0] for r,c in cm.items()}
            N=new[n]
            img=[[Q[y][x] if (y<2 or y>13 or x<2 or x>13) else m[N[y][x]] for x in range(16)] for y in range(16)]
            for (tt,ox,oy) in ((t,0,0),(t+1,8,0),(t+w,0,8),(t+w+1,8,8)):
                put_tile(d,tt,[[img[oy+y][ox+x] for x in range(8)] for y in range(8)])
            done+=1; report.append(('%02X:%04X'%(b,a),n,hex(t),w))
        assert done==3,('%02X:%04X'%(b,a),done)
        report.append(('%02X:%04X'%(b,a),'banners',banners(d,orig)))
        blob=compress(bytes(d))
        bank=0x80|((pos>>15)&0x7F); addr=0x8000|(pos&0x7FFF)
        rom[pos:pos+len(blob)]=blob
        rom[ent:ent+4]=struct.pack('<HH',addr,bank&0x7F)
        pos+=len(blob)
    assert pos<0x200000
    return report,hex(pos)

# ---- the red shop banner (だんご "dango") -> a picture of three dumplings on a skewer ----
BANNER_REFS=[  # (tileset, 8 tile ids as (left,right) per 8px row, cloth colours, text colours, base, ball, stick)
 ((0x21,0xFAF7),[0x21a,0x21b,0x228,0x229,0x236,0x237,0x238,0x239],{4,5,6,7,8},{4,5},7,5,4),
 ((0x22,0xE0AF),[0x164,0x165,0x173,0x174,0x166,0x167,0x175,0x176],{6,7,0xe,0xf},{0xe,0xf},6,0xf,0xe),
]
def canon0(t):
    m={0:0}; return tuple(m.setdefault(v,len(m)) for row in t for v in row)
_BREF=None
def _brefs(orig):
    global _BREF
    if _BREF is None:
        _BREF=[]
        for src,ids,cloth,text,base,ball,stick in BANNER_REFS:
            T=tiles_of(decompress(orig,lo(*src))[0])
            _BREF.append(([T[i] for i in ids],cloth,text,base,ball,stick))
    return _BREF
def banner_design(img,cloth,text,base,ball,stick):
    img=[r[:] for r in img]
    for y in range(32):
        for x in range(16):
            if img[y][x] in text: img[y][x]=base
    ext={}
    for y in range(26):
        xs=[x for x in range(16) if img[y][x] in cloth]
        if len(xs)>=5: ext[y]=(min(xs),max(xs))
    ys=sorted(ext)
    top,bot=ys[0]+2,ys[-1]-1
    balls=[top+3,top+3+6,top+3+12]
    for y in range(top,bot+1):
        if y not in ext: continue
        l,r=ext[y]; c=(l+r)//2
        img[y][c]=stick
        for by in balls:
            dy=y-by
            if abs(dy)<=2:
                half=2 if abs(dy)<2 else 1
                for x in range(c-half,c+half+1):
                    if l<=x<=r: img[y][x]=ball
    return img
def banners(d,orig):
    T=tiles_of(d); n=0
    for refT,cloth,text,base,ball,stick in _brefs(orig):
        cands=[[i for i,t in enumerate(T) if canon0(t)==canon0(rt)] for rt in refT]
        if not all(cands[:6]): continue
        for combo in [tuple(c[0] if c else None for c in cands)]:
            img=[[0]*16 for _ in range(32)]; ref=[[0]*16 for _ in range(32)]
            for k,(ti,rt) in enumerate(zip(combo,refT)):
                ox=(k%2)*8; oy=(k//2)*8
                if ti is None: ti_rows=rt
                else: ti_rows=T[ti]
                for y in range(8):
                    for x in range(8): img[oy+y][ox+x]=ti_rows[y][x]; ref[oy+y][ox+x]=rt[y][x]
            from collections import Counter
            cm={}
            for y in range(32 if combo[6] is not None else 24):
                for x in range(16): cm.setdefault(ref[y][x],Counter())[img[y][x]]+=1
            m={r:c.most_common(1)[0][0] for r,c in cm.items()}
            for v in (base,ball,stick): assert v in m
            new=banner_design(ref,cloth,text,base,ball,stick)
            for k,ti in enumerate(combo):
                if ti is None: continue
                ox=(k%2)*8; oy=(k//2)*8
                put_tile(d,ti,[[m[new[oy+y][ox+x]] for x in range(8)] for y in range(8)])
            n+=1
    return n
