"""Render a raw 32x32 tilemap from ROM using an 8x8 font. Only tiles 0x100-0x1FF are drawn (text layer).
render_map.py ROM MAP_OFFSET OUT.png [FONT_OFFSET=1B000] [colmajor=1]"""
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from tiles import tile
from PIL import Image
d=open(sys.argv[1],'rb').read(); m=int(sys.argv[2],16)
font=int(sys.argv[4],16) if len(sys.argv)>4 else 0x1B000
colmajor=(sys.argv[5]!='0') if len(sys.argv)>5 else True
im=Image.new('L',(256,256))
for i in range(1024):
    w=d[m+2*i]|d[m+2*i+1]<<8; t=w&0x3FF
    if not 0x100<=t<0x200: continue
    c,r=(i//32,i%32) if colmajor else (i%32,i//32)
    px=tile(d,font+(t-0x100)*32,4)
    hf=w&0x4000; vf=w&0x8000
    for y in range(8):
        for x in range(8):
            v=px[7-y if vf else y][7-x if hf else x]
            if v: im.putpixel((c*8+x,r*8+y),255)
im.resize((512,512),Image.NEAREST).save(sys.argv[3])
