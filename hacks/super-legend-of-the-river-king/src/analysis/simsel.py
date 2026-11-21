import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import sim
rom=open(P.out('knt2_en.sfc'),'rb').read()
c=sim.make_cpu(rom)
c.hooks[(0x00,0xDA52)]=c.hooks[(0x00,0xDA6A)]
for i in range(9): c.wram[0x086A+i]=0
c.wr16(0,0x0860,1)
def mul(cpu):
    cpu.wr16(0,0x46,(cpu.rd16(0,0x3E)*cpu.rd16(0,0x42))&0xFFFF)
    cpu.PC=(cpu.pull16()+1)&0xFFFF; cpu.PB=cpu.pull()
c.hooks[(0x00,0xDA42)]=mul
def press(row,col):
    c.wram[0x1F000+0x2C30-0xF000+0xF000-0xF000]  # noop
    c.wr16(0x7F,0x2C30,col); c.wr16(0x7F,0x2C32,row)
    c.wr16(0,0x134A,0x0080)
    for i in range(0x600): c.wram[0x1F000+i]=0
    c.m=0;c.x=0;c.D=0;c.DB=0x81
    c.call(0x81,0xB353)
seq=[(1,9),(4,0),(5,8),(6,9),(5,9),(7,3),(11,0),(9,9)]
for r,cc in seq: press(r,cc)
print(bytes(c.wram[0x086A:0x0874]), c.rd16(0,0x16C0))
im=sim.render_stage(c,rows=1,cols=10); im.resize((im.size[0]*4,im.size[1]*4)).save(P.out('name.png'))
press(0,7); print('after BS',bytes(c.wram[0x086A:0x0874]))
