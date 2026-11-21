import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import sim
from PIL import Image
rom=open(P.out('knt2_en.sfc'),'rb').read()
def lines(c,n=3):
    img=Image.new('L',(128,16*n)); px=img.load()
    for L in range(n):
      for t in range(16):
        for h in range(2):
          for y in range(8):
            p0=c.wram[0x1F000+L*0x200+h*0x100+t*16+2*y+1]
            for x in range(8):
              if (p0>>(7-x))&1: px[t*8+x,L*16+h*8+y]=255
    return img
def run(s,path):
    c=sim.make_cpu(rom); del c.hooks[(0,0xDA4E)]
    c.wram[0x2000:0x2000+len(s)]=s; c.wr16(0,0x1A7B,100)
    c.wr16(0,0x0A,0x2000); c.wr16(0,0x0C,0x7E)
    c.m=0;c.x=0;c.D=0;c.DB=0x82
    c.call(0x82,0x854E)
    lines(c).resize((384,144)).save(path)
run(b'\xdfHeader\xcc\xdfRedspot Trout\x0c\xda\xe0\x00',P.out('w0.png'))
