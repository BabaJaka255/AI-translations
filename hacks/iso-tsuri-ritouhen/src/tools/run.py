import cpu
BTN={'B':0x8000,'Y':0x4000,'SELECT':0x2000,'START':0x1000,'UP':0x800,'DOWN':0x400,'LEFT':0x200,'RIGHT':0x100,'A':0x80,'X':0x40,'L':0x20,'R':0x10}
class Runner:
    def __init__(self, rom, state):
        self.c=cpu.SNES(rom,state); self.rom=rom
        self.nmi=self.c.rom[0xffea]|self.c.rom[0xffeb]<<8
        self.frames=0
        def spc(c): c.io[0x2140]=c.A&0xff
        self.c.exec_hooks[0xC207BB]=spc
    def nmi_now(self):
        c=self.c
        c.push(c.PB); c.push16(c.PC); c.push(c.P)
        c.P=(c.P|4)&~8&0xff; c.PB=0; c.PC=self.nmi
    def frame(self, maxsteps=40000):
        c=self.c; n=0
        waitpc=0x825E
        while n<maxsteps:
            if c.PC==waitpc and c.PB in (0x80,0xC0,0x00) and c.wram[0xd94]|c.wram[0xd95]:
                # count loop
                break
            try:
                c.step()
            except cpu.Halt as h:
                if str(h)=='WAI': break
                raise
            n+=1
        self.nmi_now()
        # run NMI until RTI returns (stack back)
        s=c.S; m=0
        while True:
            op=c.rd(c.PB<<16|c.PC)
            c.step(); m+=1
            if op==0x40 and c.S==(s+4)&0xffff: break
            if m>200000: raise Exception('NMI stuck at %06X'%(c.PB<<16|c.PC))
        self.frames+=1
        return n
    def run(self, frames, joy=0):
        self.c.joy=joy
        for _ in range(frames): self.frame()
        self.c.joy=0
    def press(self, btn, hold=4, after=8):
        self.run(hold, BTN[btn]); self.run(after)
