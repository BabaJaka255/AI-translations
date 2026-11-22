"""Labeled 16x16 chart of 256 8x8 4bpp tiles: chart.py FILE OFFSET OUT.png"""
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from tiles import tile
from PIL import Image, ImageDraw
d=open(sys.argv[1],'rb').read(); o=int(sys.argv[2],16)
S=4; C=8*S+6
im=Image.new('RGB',(16+16*C,16+16*C),(40,40,60)); dr=ImageDraw.Draw(im)
for i in range(16):
    dr.text((16+i*C+10,2),'%X'%i,fill=(255,255,0)); dr.text((2,16+i*C+12),'%X'%i,fill=(255,255,0))
for t in range(256):
    px=tile(d,o+t*32,4); x0=16+(t%16)*C; y0=16+(t//16)*C
    for y in range(8):
        for x in range(8):
            v=px[y][x]*17
            dr.rectangle([x0+x*S,y0+y*S,x0+x*S+S-1,y0+y*S+S-1],fill=(v,v,v))
im.save(sys.argv[3])
