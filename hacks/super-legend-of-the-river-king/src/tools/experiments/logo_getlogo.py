import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
from PIL import Image
A=_o.path.join(P.ROOT,'data','dumps')+'/'  # dumps renamed: VideoRamSign.dmp etc.
v=open(A+'VideoRamTitle.dmp','rb').read()
cg=open(A+'CgRamTitle.dmp','rb').read()
def col(i):
    w=cg[2*i]|cg[2*i+1]<<8
    return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31)
OBJ=0xC000
def tile(n):
    b=OBJ+n*32; out=[[0]*8 for _ in range(8)]
    for y in range(8):
        p=[v[b+2*y],v[b+2*y+1],v[b+16+2*y],v[b+17+2*y]]
        for x in range(8):
            out[y][x]=sum(((p[k]>>(7-x))&1)<<k for k in range(4))
    return out
def logo_index():
    """192x48 index image of the logo as placed by sprite group 0."""
    img=[[0]*192 for _ in range(48)]
    def put(tn,x0,y0,size):
        for ty in range(size):
            for tx in range(size):
                t=tile(tn+ty*16+tx)
                for y in range(8):
                    for x in range(8): img[y0+ty*8+y][x0+tx*8+x]=t[y][x]
    big=[(0,0),(4,32),(8,64),(0xC,96),(0x100,128),(0x104,160)]
    for t,x in big: put(t,x,0,4)
    for i,t in enumerate([0x40,0x42,0x44,0x46,0x48,0x4a,0x4c,0x4e,0x140,0x142,0x144,0x146]): put(t,16*i,32,2)
    return img
if __name__=='__main__':
    img=logo_index()
    pal=[col(128+i) for i in range(16)]
    print(pal)
    im=Image.new('RGB',(192,48)); px=im.load()
    for y in range(48):
        for x in range(192): px[x,y]=pal[img[y][x]] if img[y][x] else (40,90,40)
    im.resize((768,192),Image.NEAREST).save('orig_logo.png')
