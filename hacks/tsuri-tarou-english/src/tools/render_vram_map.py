"""Render a ROM tilemap (32x32, col- or row-major) with the tile data of a savestate's VRAM.
render_vram_map.py ROM STATE MAP_OFF CHARBASE_WORD BPP OUT.png [colmajor 0/1]"""
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
import s9xstate as S
from tiles import tile
from PIL import Image
rom=open(sys.argv[1],'rb').read(); v=S.get(open(sys.argv[2],'rb').read(),'VRA')
m=int(sys.argv[3],16); cb=int(sys.argv[4],16)*2; bpp=int(sys.argv[5]); out=sys.argv[6]
col=len(sys.argv)>7 and sys.argv[7]=='1'
im=Image.new('L',(256,256)); mx=(1<<bpp)-1
for i in range(1024):
    w=rom[m+2*i]|rom[m+2*i+1]<<8; t=w&0x3FF
    c,r=(i//32,i%32) if col else (i%32,i//32)
    px=tile(v,(cb+t*8*bpp)&0xFFFF,bpp)
    for y in range(8):
        for x in range(8):
            p=px[7-y if w&0x8000 else y][7-x if w&0x4000 else x]
            im.putpixel((c*8+x,r*8+y),p*255//mx)
im.save(out)
