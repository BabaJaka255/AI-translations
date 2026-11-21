import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
def sheet(d,bpp,cols=32,scale=2):
    n=len(d)//(8*bpp); rows=(n+cols-1)//cols
    img=Image.new('L',(cols*8,rows*8)); px=img.load()
    for t in range(n):
        base=t*8*bpp
        for y in range(8):
            pl=[d[base+(p//2)*16+2*y+(p%2)] for p in range(bpp)]
            for x in range(8):
                v=sum(((pl[p]>>(7-x))&1)<<p for p in range(bpp))
                px[(t%cols)*8+x,(t//cols)*8+y]=v*255//((1<<bpp)-1)
    return img.resize((img.size[0]*scale,img.size[1]*scale),Image.NEAREST)
if __name__=='__main__':
    b,a,bpp=int(sys.argv[1],16),int(sys.argv[2],16),int(sys.argv[3])
    d,_=lzss.decompress(rom,lzss.lo(b,a))
    sheet(d,bpp).save(sys.argv[4])
