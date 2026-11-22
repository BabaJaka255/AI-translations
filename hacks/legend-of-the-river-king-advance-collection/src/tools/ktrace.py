import sys;sys.path.insert(0,'.')
from drive import *
from unicorn import *
from unicorn.arm_const import *
from collections import defaultdict
def trace_reads(g,frames,lo=0x08000000,hi=0x08400000):
    reads=defaultdict(list)
    def hk(uc,acc,addr,size,val,ud):
        reads[uc.reg_read(UC_ARM_REG_PC)].append((addr,size))
    h=g.uc.hook_add(UC_HOOK_MEM_READ,hk,begin=lo,end=hi)
    g.run_frames(frames)
    g.uc.hook_del(h)
    res=[]
    for pc,l in reads.items():
        addrs=sorted(set(a for a,s in l))
        res.append((len(l),pc,len(addrs),addrs,set(s for a,s in l),l))
    res.sort(key=lambda r:-r[2])
    return res
