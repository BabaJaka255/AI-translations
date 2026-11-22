"""Render label art stored as rows of W tiles (top halves) followed by W tiles (bottom halves)."""
import sys
from PIL import Image,ImageDraw
def render(d,W,out,scale=2,base=0):
    rowb=W*32; nrows=len(d)//rowb
    im=Image.new('RGB',(W*8+60,nrows*16),(0,0,90)); pal=[(0,0,90),(255,255,255),(120,120,200),(255,255,0)]
    for r in range(nrows):
        for half in range(2):
            for t in range(W):
                o=r*rowb+half*W*16+t*16
                for y in range(8):
                    lo,hi=d[o+2*y],d[o+2*y+1]
                    for x in range(8):
                        im.putpixel((60+t*8+x,r*16+half*8+y),pal[((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)])
    dr=ImageDraw.Draw(im)
    for r in range(nrows): dr.text((0,r*16+3),'%05X'%(base+r*rowb),fill=(255,90,90))
    im.resize((im.width*scale,im.height*scale),Image.NEAREST).save(out)
if __name__=='__main__':
    rom=open(sys.argv[1],'rb').read(); a=int(sys.argv[2],16); b=int(sys.argv[3],16)
    render(rom[a:b],int(sys.argv[4]),sys.argv[5],base=a)
