import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
from PIL import Image, ImageFont, ImageDraw
import getlogo,sys
W,H=192,48
pal=[getlogo.col(128+i) for i in range(16)]
def mask_text(text,font,size,stretch=1.0):
    f=ImageFont.truetype(font,size)
    bb=f.getbbox(text)
    im=Image.new('1',(bb[2]-bb[0]+4,bb[3]-bb[1]+4),0)
    ImageDraw.Draw(im).text((2-bb[0],2-bb[1]),text,font=f,fill=1)
    if stretch!=1.0: im=im.resize((int(im.size[0]*stretch),im.size[1]),Image.NEAREST)
    bb=im.getbbox(); return im.crop(bb)
def style(body,y0,y1,img):
    """body: set of (x,y). writes indices into img."""
    bands=[2,3,4,5,6,7]
    N=lambda x,y:[(x+dx,y+dy) for dx in (-1,0,1) for dy in (-1,0,1) if dx or dy]
    for (x,y) in body:
        t=(y-y0)/max(1,(y1-y0))
        v=bands[min(5,int(t*6))]
        if (x+1,y) in body and (x+2,y) not in body and (x,y-1) in body: v=10
        edge=any(p not in body for p in N(x,y))
        if edge and t>0.6: v=13
        img[y][x]=v
    for (x,y) in body:
        for p in N(x,y):
            px,py=p
            if p not in body and 0<=px<W and 0<=py<H and img[py][px]==0: img[py][px]=15
def build(font,lines):
    img=[[0]*W for _ in range(H)]
    for text,size,x,y,stretch in lines:
        m=mask_text(text,font,size,stretch)
        body=set()
        mw,mh=m.size; pxm=m.load()
        if x=='c': x=(W-mw)//2
        for yy in range(mh):
            for xx in range(mw):
                if pxm[xx,yy] and 0<=x+xx<W and 0<=y+yy<H: body.add((x+xx,y+yy))
        style(body,y,y+mh-1,img)
        print(text,'size',mw,mh)
    return img
def save(img,path):
    im=Image.new('RGB',(W,H)); px=im.load()
    for y in range(H):
        for x in range(W): px[x,y]=pal[img[y][x]] if img[y][x] else (40,90,40)
    im.resize((W*4,H*4),Image.NEAREST).save(path)
