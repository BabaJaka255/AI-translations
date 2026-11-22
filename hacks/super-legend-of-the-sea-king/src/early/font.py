import sys
from PIL import Image
rom=open(sys.argv[1],'rb').read(); base=int(sys.argv[2],16); n=int(sys.argv[3]); out=sys.argv[4]
cols=16; rows=(n+cols-1)//cols
im=Image.new('L',(cols*17,rows*17),128)
for g in range(n):
    o=base+(g&0xFF8)*32+(g&7)*16
    for qy in range(2):
      for qx in range(2):
        t=o+qy*0x80+qx*8
        for y in range(8):
            b=rom[t+y]
            for x in range(8):
                im.putpixel(((g%cols)*17+qx*8+x,(g//cols)*17+qy*8+y),0 if b&(0x80>>x) else 255)
im=im.resize((im.width*2,im.height*2),Image.NEAREST); im.save(out)
