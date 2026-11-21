import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import sim
from PIL import Image
class Stop(Exception): pass
def run(romb, entry):
    c=sim.make_cpu(romb)
    def stop(cpu): raise Stop()
    c.hooks[(0x00,0xDA52)]=stop
    for i in range(0x1000): c.wram[0x1F000+i]=0
    c.m=0;c.x=0;c.D=0;c.DB=0x81
    c.wr16(0,0x0860,1)
    try: c.call(0x81,entry)
    except Stop: pass
    return c
def show(c,n,path):
    lines=n//0x200
    img=Image.new('RGB',(16*8,lines*16)); px=img.load()
    pal=[(0,0,0),(255,0,0),(255,255,255),(0,255,0)]
    for L in range(lines):
      for t in range(16):
        for h in range(2):
          base=0x1F000+L*0x200+h*0x100+t*0x10
          for y in range(8):
            p0=c.wram[base+2*y]; p1=c.wram[base+2*y+1]
            for x in range(8):
              v=((p0>>(7-x))&1)|(((p1>>(7-x))&1)<<1)
              px[t*8+x,L*16+h*8+y]=pal[v]
    img.resize((img.size[0]*3,img.size[1]*3),Image.NEAREST).save(path)
if __name__=='__main__':
    rom=open(sim.ROM,'rb').read()
    c=run(rom,0xAF2E); show(c,0xC00,P.out('pal10.png'))
    import collections
    print(collections.Counter(c.wram[0x1F000+i] for i in range(0,0xC00,2)).most_common(3))
    print(collections.Counter(c.wram[0x1F001+i] for i in range(0,0xC00,2)).most_common(3))
