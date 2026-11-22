import sys,pickle
from PIL import Image,ImageDraw,ImageFont
rom=open(sys.argv[1],'rb').read(); g0=int(sys.argv[2],16); g1=int(sys.argv[3],16); out=sys.argv[4]
T={}
for l in open(sys.argv[5],encoding='utf-8'):
    l=l.strip()
    if '=' in l and not l.startswith('#'): a,b=l.split('=',1); T[int(a,16)&0xFFF]=b
F=ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',40)
S=3; cols=8; cw=150; ch=56
n=g1-g0; rows=(n+cols-1)//cols
im=Image.new('RGB',(cols*cw,rows*ch),'white'); d=ImageDraw.Draw(im)
for k in range(n):
    g=g0+k; o=0x40000+(g&0xFF8)*32+(g&7)*16
    X=(k%cols)*cw; Y=(k//cols)*ch
    d.rectangle([X,Y,X+cw-1,Y+ch-1],outline='#ccc')
    d.text((X+2,Y+2),'%03X'%g,fill='red')
    for qy in range(2):
      for qx in range(2):
        for y in range(8):
          b=rom[o+qy*0x80+qx*8+y]
          for x in range(8):
            if b&(0x80>>x): d.rectangle([X+30+(qx*8+x)*S,Y+4+(qy*8+y)*S,X+30+(qx*8+x)*S+S-1,Y+4+(qy*8+y)*S+S-1],fill='black')
    if g in T: d.text((X+86,Y+4),T[g],font=F,fill='blue')
    else: d.text((X+86,Y+14),'??',fill='orange')
im.save(out)
