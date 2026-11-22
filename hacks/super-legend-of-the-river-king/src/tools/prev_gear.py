import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
from gear_placeholders import SLOTS,rd
from PIL import Image
orig=open(sys.argv[1],'rb').read(); new=open(sys.argv[2],'rb').read()
pal={1:(40,60,120),0xF:(255,255,255)}
S=6; im=Image.new('RGB',(5*40*S,2*36*S),(0,0,0))
for i,(base,tr,tc,w,h,t,v) in enumerate(SLOTS):
  for j,src in enumerate((orig,new)):
    for r in range(h):
      for c in range(w):
        tl=rd(src,base+(tr+r)*0x200+(tc+c)*32)
        for y in range(8):
          for x in range(8):
            col=pal.get(tl[y][x],(255,0,0))
            for a in range(S):
              for b in range(S): im.putpixel((i*40*S+(c*8+x)*S+a, j*36*S+(r*8+y)*S+b),col)
im.save(sys.argv[3])
