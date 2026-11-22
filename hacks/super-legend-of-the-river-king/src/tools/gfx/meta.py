import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
def tile(d,t):
    b=t*32
    return [[sum(((d[b+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)]
def meta_sheet(d,cols=16,scale=3,mode='seq4'):
    n=len(d)//32//4
    rows=(n+cols-1)//cols
    img=Image.new('L',(cols*16,rows*16)); px=img.load()
    for m in range(n):
        for q in range(4):
            t=tile(d,m*4+q); ox=(m%cols)*16+(q%2)*8; oy=(m//cols)*16+(q//2)*8
            for y in range(8):
                for x in range(8): px[ox+x,oy+y]=t[y][x]*17
    return img.resize((img.size[0]*scale,img.size[1]*scale),Image.NEAREST)
if __name__=='__main__':
    b,a=int(sys.argv[1],16),int(sys.argv[2],16)
    d,_=lzss.decompress(rom,lzss.lo(b,a))
    meta_sheet(d).save(sys.argv[3])
