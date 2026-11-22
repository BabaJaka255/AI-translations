"""Run the game's CPU from a snes9x savestate in the simple interpreter and log ROM data reads.
trace.py ROM STATE STEPS [minbank]
Hardware reads return safe values; the frame wait loop at $00:9724 is released at once."""
import sys, collections
sys.path.insert(0,__import__('os').path.dirname(__file__))
import s9xstate as S
from cpu65816 import CPU
rom=open(sys.argv[1],'rb').read(); st=open(sys.argv[2],'rb').read(); steps=int(sys.argv[3])
reg=S.get(st,'REG'); be=lambda i:reg[i]<<8|reg[i+1]
APU={}; REGS={}; HW=[]; DMA=[]
class T(CPU):
    def wr(self,bank,addr,v):
        a=addr&0xFFFF
        if (bank&0x7F)<0x40 and 0x2140<=a<0x2144: APU[a]=v&0xFF
        if (bank&0x7F)<0x40 and (0x2100<=a<0x2140 or 0x4300<=a<0x4380):
            REGS[a]=v&0xFF
            if a in (0x2105,0x2107,0x2108,0x2109,0x210B,0x210C,0x212C,0x2116,0x2117): HW.append((self.cur,a,v&0xFF))
        if (bank&0x7F)<0x40 and a==0x420B:
            for ch in range(8):
                if v>>ch&1:
                    b=0x4300+ch*16; g=lambda o:REGS.get(b+o,0)
                    src=g(4)<<16|g(3)<<8|g(2); n=g(6)<<8|g(5); dest=g(1)
                    DMA.append((self.cur,ch,'%06X'%src,n or 0x10000,'%02X'%(0x2100|dest),'%04X'%(REGS.get(0x2117,0)<<8|REGS.get(0x2116,0)),'%02X'%REGS.get(0x2115,0)))
        super().wr(bank,addr,v)
    fetching=False
    def fetch(self,n):
        self.fetching=True; v=super().fetch(n); self.fetching=False; return v
    def rd(self,bank,addr):
        bank&=0xFF; addr&=0xFFFF
        if (bank&0x7F)<0x40 and 0x2000<=addr<0x8000:
            if addr==0x4212: self.t=getattr(self,'t',0)^0x81; return self.t
            if 0x2140<=addr<0x2144: return APU.get(addr,0)
            return 0
        v=super().rd(bank,addr)
        if addr>=0x8000 and not self.fetching and bank not in (0x7E,0x7F) and not (bank==self.PB and addr==self.PC):
            off=((bank&0x7F)<<15)|(addr&0x7FFF)
            LOG[(off,self.cur)]+=1
        return v
LOG=collections.Counter()
c=T(rom,S.get(st,'RAM'))
c.hooks[(0,0x9E32)]=lambda cpu:(setattr(cpu,'PC',(cpu.pull16()+1)&0xFFFF),setattr(cpu,'PB',cpu.pull()))
c.PB=reg[0]; c.DB=reg[1]; c.setP(be(2)); c.A=be(4); c.D=be(6); c.S=be(8); c.X=be(10); c.Y=be(12); c.PC=be(14)
PCS=collections.Counter(); NMIS=[0]
for i in range(steps):
    PCS[(c.PB,c.PC)]+=1
    c.cur=(c.PB<<16)|c.PC
    if c.PB==0 and c.PC==0x9724 and c.wram[0x800]==0 and not c.I:
        c.push(c.PB); c.push16(c.PC); c.push(c.P()); c.PB=0; c.PC=rom[0x7FEA]|rom[0x7FEB]<<8; c.I=1; c.Dm=0; NMIS[0]+=1
    try: c.step()
    except Exception as e: print('stop',e,'%02X:%04X'%(c.PB,c.PC)); break
byoff=collections.defaultdict(set)
for (off,pc),n in LOG.items(): byoff[pc].add(off)
for pc in sorted(byoff):
    offs=sorted(byoff[pc]); print('%06X reads %4d  ROM %06X-%06X'%(pc,len(offs),offs[0],offs[-1]))
print('log',len(LOG)); print('nmis',NMIS[0]); print('end at %02X:%04X steps %d'%(c.PB,c.PC,c.steps))
print(sorted(PCS.items(),key=lambda x:-x[1])[:15])
print(sorted(set('%02X:%04X'%k for k in PCS))[:400])

import os
if os.environ.get('HW'):
    for h in HW: print('HW %06X %04X=%02X'%h)
    for d in DMA: print('DMA %06X ch%d src %s len %X -> %s vram %s vmain %s'%d)
