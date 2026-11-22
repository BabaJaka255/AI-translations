"""Render raw tile data as an image. tiles.py FILE OFFSET COUNT BPP OUT.png [cols]"""
import sys
from PIL import Image
def tile(d,o,bpp):
    px=[[0]*8 for _ in range(8)]
    for y in range(8):
        for p in range(bpp):
            base=o+(p//2)*16+y*2+(p&1) if bpp>1 else o+y
            b=d[base] if base<len(d) else 0
            for x in range(8):
                if b>>(7-x)&1: px[y][x]|=1<<p
    return px
def render(d,o,n,bpp,cols=16,scale=2):
    rows=(n+cols-1)//cols; im=Image.new('L',(cols*8,rows*8))
    mx=(1<<bpp)-1; sz=8*bpp
    for t in range(n):
        px=tile(d,o+t*sz,bpp)
        for y in range(8):
            for x in range(8): im.putpixel(((t%cols)*8+x,(t//cols)*8+y),px[y][x]*255//mx)
    return im.resize((im.width*scale,im.height*scale),Image.NEAREST)
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); o=int(sys.argv[2],16); n=int(sys.argv[3]); bpp=int(sys.argv[4])
    cols=int(sys.argv[6]) if len(sys.argv)>6 else 16
    render(d,o,n,bpp,cols).save(sys.argv[5])
