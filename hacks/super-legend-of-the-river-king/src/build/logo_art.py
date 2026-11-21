import paths as P
from PIL import Image, ImageFont, ImageDraw
W,H=192,48
F_TEAL=P.font('Poppins-Bold.ttf')
F_RED=P.font('Poppins-BoldItalic.ttf')
PAL={0:(40,90,40),1:(100,16,8),2:(255,236,90),3:(255,206,50),4:(255,166,30),5:(250,120,24),6:(232,72,24),7:(200,40,24),
     8:(176,220,248),9:(255,255,255),10:(255,255,200),11:(16,64,64),12:(56,176,150),13:(120,220,190),14:(115,115,115),15:(104,160,216)}
def glyph_mask(ch,font,size,stretch=1.0):
    f=ImageFont.truetype(font,size); bb=f.getbbox(ch)
    if bb[2]<=bb[0]: return None,f.getlength(ch)
    im=Image.new('L',(bb[2]-bb[0]+8,size*2),0)
    ImageDraw.Draw(im).text((4-bb[0],0),ch,font=f,fill=255)
    if stretch!=1: im=im.resize((max(1,int(im.size[0]*stretch)),im.size[1]),Image.LANCZOS)
    return im.point(lambda v:255 if v>110 else 0).convert('1'),None
def word_mask(text,font,size,stretch=1.0,bounce=None,track=0):
    """returns set of (x,y) with baseline-relative y, per-letter bounce offsets."""
    f=ImageFont.truetype(font,size)
    pts=set(); x=0
    for i,ch in enumerate(text):
        adv=f.getlength(ch)*stretch
        m,_=glyph_mask('\u0131' if ch=='i' else ch,font,size,stretch)
        if m is not None:
            dy=bounce[i] if bounce else 0
            bb=ImageFont.truetype(font,size).getbbox(ch)
            px=m.load()
            for yy in range(m.size[1]):
                for xx in range(m.size[0]):
                    if px[xx,yy]: pts.add((int(x+(bb[0])*stretch)+xx-4,yy+dy))
            if ch=='i':
                gp=[(xx,yy) for yy in range(m.size[1]) for xx in range(m.size[0]) if px[xx,yy]]
                top=min(y for _,y in gp); cols=[xx for xx,yy in gp if yy==top+1]
                ox=int(x+(bb[0])*stretch)-4
                dh=max(3,len(cols)-1)
                for yy in range(top-dh-2,top-2):
                    for xx in cols: pts.add((ox+xx+(top-yy)//4,yy+dy))
        x+=adv+track
    return pts
def normalize(pts):
    minx=min(x for x,_ in pts); miny=min(y for _,y in pts)
    return {(x-minx,y-miny) for x,y in pts}
def bbox(pts): return (max(x for x,_ in pts)+1,max(y for _,y in pts)+1)
def shift(pts,dx,dy): return {(x+dx,y+dy) for x,y in pts}
N8=[(dx,dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]
def ring(pts,occupied):
    r=set()
    for x,y in pts:
        for dx,dy in N8:
            p=(x+dx,y+dy)
            if p not in occupied: r.add(p)
    return r
def make(params):
    img=[[0]*W for _ in range(H)]
    # red line
    red=normalize(word_mask('River King',F_RED,params['rs'],params['rst'],bounce=params['bounce'],track=params['rtrack']))
    rw,rh=bbox(red)
    the=normalize(word_mask('The',F_RED,params['ts'],1.0,track=0))
    tw,th=bbox(the)
    teal=normalize(word_mask('Super Legend of',F_TEAL,params['gs'],params['gst'],track=params['gtrack']))
    gw,gh=bbox(teal)
    total=tw+params['thegap']+rw
    x0=(W-total)//2
    ry=H-3-1-rh            # sticker 2 + outline 1 at bottom
    red=shift(red,x0+tw+params['thegap'],ry)
    the=shift(the,x0,ry+params['they'])
    teal=shift(teal,(W-gw)//2+params['gdx'],3+1)

    # paint red & The: gradient by y over red line extent
    y0=min(y for _,y in red); y1=max(y for _,y in red)
    for body in (red,the):
        for (x,y) in body:
            t=(y-y0)/max(1,y1-y0); v=[2,3,4,5,6,7][max(0,min(5,int(t*6)))]
            if (x,y-1) not in body and (x,y-2) not in body: v=10
            if 0<=x<W and 0<=y<H: img[y][x]=v
        for (x,y) in ring(body,body):
            if 0<=x<W and 0<=y<H and img[y][x]==0: img[y][x]=1
    tealo=ring(teal,teal)
    for (x,y) in tealo:
        if 0<=x<W and 0<=y<H: img[y][x]=11
    for (x,y) in teal:
        if 0<=x<W and 0<=y<H: img[y][x]=13 if (x,y-1) not in teal or (x,y-2) not in teal else 12
    occ={(x,y) for y in range(H) for x in range(W) if img[y][x]}
    s1=ring(occ,occ); occ2=occ|s1; s2=ring(s1,occ2)
    for (x,y) in s1:
        if 0<=x<W and 0<=y<H: img[y][x]=8
    for (x,y) in s2:
        if 0<=x<W and 0<=y<H: img[y][x]=15
    return img
P=dict(rs=32,rst=0.9,bounce=[0,-1,1,-1,1,0,0,-1,1,-1],rtrack=0,ts=13,thegap=1,they=6,gs=15,gst=1.0,gtrack=1,gdx=8)
