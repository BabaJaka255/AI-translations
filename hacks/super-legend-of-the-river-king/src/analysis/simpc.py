import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import sim
from PIL import Image
rom=open(P.out('knt2_en.sfc'),'rb').read()
def mul(cpu):
    cpu.wr16(0,0x46,(cpu.rd16(0,0x3E)*cpu.rd16(0,0x42))&0xFFFF); cpu.PC=(cpu.pull16()+1)&0xFFFF; cpu.PB=cpu.pull()
c=sim.make_cpu(rom); c.hooks[(0,0xDA42)]=mul
for h in (0xDA52,0xDA8A): c.hooks[(0,h)]=c.hooks[(0,0xDA6A)]
for i in range(0xA0): c.wram[0x12B90+i]=0
def prep():
    c.m=0;c.x=0;c.D=0;c.DB=0x81
    c.call(0x81,0xEFF9)
def key(mode,row,col):
    prep()
    c.wr16(0x7F,0x2C3A,mode); c.wr16(0x7F,0x2C32,row); c.wr16(0x7F,0x2C30,col)
    c.m=0;c.x=0;c.D=0;c.DB=0x81
    if row>=2: c.call(0x81,0xF3F8)
    elif row==1: c.call(0x81,0xF0CD)
    else: c.call(0x81,0xED7A)
seq=[(0,2,7),(1,2,4),(1,3,1),(1,3,1),(1,2,4),(0,0,7),(0,1,4),(0,1,1),(0,0,1),(0,0,2),(0,0,3),(2,3,8),(0,0,8),(0,2,0)]
for s in seq: key(*s)
prep()
print(bytes(c.wram[0x12B90:0x12BB0]), 'units',c.rd16(0x7F,0x2C3C),'line',c.rd16(0x7F,0x2C3E))
c.call(0x81,0xF199)
def lines(c,n=4):
    img=Image.new('L',(256,16*n)); px=img.load()
    for L in range(n):
      for t in range(32):
        off=L*0x400+(t//16)*0x200+(t%16)*0x10
        for h in range(2):
          for y in range(8):
            b=c.wram[0x1F000+off+h*0x100+2*y+1]|c.wram[0x1F000+off+h*0x100+2*y]
            for x in range(8):
              if (b>>(7-x))&1: px[t*8+x,L*16+h*8+y]=255
    return img
lines(c).resize((768,192)).save(P.out('msg.png'))
def lines2(c,n=4):
    img=Image.new('L',(256,16*n)); px=img.load()
    for L in range(n):
      for t in range(32):
        off=L*0x400+(t//16)*0x200+(t%16)*0x10
        for h in range(2):
          for y in range(8):
            p0=c.wram[0x1F000+off+h*0x100+2*y]; p1=c.wram[0x1F000+off+h*0x100+2*y+1]
            for x in range(8):
              v=((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1)
              px[t*8+x,L*16+h*8+y]=v*80
    return img
lines2(c).resize((768,192)).save(P.out('msg.png'))
