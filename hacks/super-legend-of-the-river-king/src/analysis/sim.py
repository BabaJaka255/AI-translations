import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,struct
sys.path.insert(0,P.BUILD); sys.path.insert(0,P.ANALYSIS)
from cpu65816 import CPU
from PIL import Image
ROM=P.ROM
WRAMDUMP=P.WRAM
def table():
    rom=open(ROM,'rb').read()
    return [struct.unpack('<H',rom[0x10A22+2*i:0x10A22+2*i+2])[0] for i in range(64)]
TBL=table()
def make_cpu(rom=None,wram=None):
    rom=rom or open(ROM,'rb').read()
    w=bytearray(open(WRAMDUMP,'rb').read()) if wram is None else wram
    c=CPU(rom,w)
    # no-op the wait/DMA/etc long calls
    for addr in (0xDA26,0xDA6A,0xDA4E,0xE2B4):
        c.hooks[(0x00,addr)]=lambda cpu:(setattr(cpu,'PC',(cpu.pull16()+1)&0xFFFF),setattr(cpu,'PB',cpu.pull()))
    c.wram[0x134A]=0x80; c.wram[0x134B]=0x80   # pretend button held (passes ▼ waits)
    c.wram[0x1348]=0x00
    return c
def render_stage(c,rows=2,cols=24,scale=1):
    """Dialog staging buffer -> image. Column P (8px) uses TBL[P] (upper tile) and +0x100 (lower tile); plane 1 only."""
    img=Image.new('L',(cols*8,rows*16),0); px=img.load()
    buf=0x1F000
    for r in range(rows):
        for p in range(cols):
            off=TBL[24*r+p]
            for half in range(2):
                for y in range(8):
                    b=c.wram[buf+off+0x100*half+2*y]
                    for x in range(8):
                        if (b>>(7-x))&1: px[p*8+x, r*16+half*8+y]=255
    return img
def run_dialog(c,ptr,bank=5,entry=(0x82,0x8B47)):
    # clear staging buffer region, set pointer and run
    for i in range(0x600): c.wram[0x1F000+i]=0
    c.wr16(0,0x0A,ptr); c.wr16(0,0x0C,bank)
    c.wr16(0,0x10,0)
    c.m=0; c.x=0; c.D=0; c.DB=0x82
    c.call(entry[0],entry[1])
if __name__=="__main__":
    c=make_cpu()
    ptr=0xC265-0x0   # placeholder
    # string [021] at ROM 0x2C24B -> snes 05:C24B
    run_dialog(c,0xC24B)
    im=render_stage(c); im.resize((im.size[0]*4,im.size[1]*4),Image.NEAREST).save(P.out('sim_orig.png'))
    print("steps",c.steps)
