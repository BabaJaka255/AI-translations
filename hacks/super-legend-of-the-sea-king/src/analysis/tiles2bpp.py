"""Render 2bpp data as a tile sheet: python3 tiles2bpp.py file_or_bank:addr out.png [cols] [8x16]"""
import sys
from PIL import Image,ImageDraw
def render(d,out,cols=16,tall=False,scale=3,labels=True):
    n=len(d)//16; rows=(n+cols-1)//cols
    if tall: rows=((n//(2*cols))+1)*2
    im=Image.new('RGB',(cols*8,rows*8),(0,0,90))
    pal=[(0,0,90),(255,255,255),(120,120,200),(255,255,0)]
    for t in range(n):
        o=t*16; tx=(t%cols); ty=(t//cols)
        for y in range(8):
            lo,hi=d[o+2*y],d[o+2*y+1]
            for x in range(8):
                c=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
                im.putpixel((tx*8+x,ty*8+y),pal[c])
    im=im.resize((im.width*scale,im.height*scale),Image.NEAREST)
    if labels:
        dr=ImageDraw.Draw(im)
        for r in range(rows): dr.text((0,r*8*scale),'%X'%(r*cols),fill=(255,80,80))
    im.save(out)
if __name__=='__main__':
    sys.path.insert(0,__import__('os').path.join(__import__('os').path.dirname(__file__),'..','build'))
    import lzss,paths
    a=sys.argv[1]
    if ':' in a:
        rom=open(paths.ROM,'rb').read(); b,ad=a.split(':'); d,_=lzss.decompress(rom,lzss.lo(int(b,16),int(ad,16)))
    else: d=open(a,'rb').read()
    render(d,sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 16)
