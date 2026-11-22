import struct,sys
from capstone import *
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
r=open('../rom/k34.gba','rb').read()
def bl_callers(target,lo=0,hi=0x200000):
    out=[]
    for o in range(lo,hi,2):
        h1,h2=struct.unpack_from('<HH',r,o)
        if h1>>11==0x1e and h2>>11==0x1f:
            off=((h1&0x7ff)<<12)|((h2&0x7ff)<<1)
            if off&0x400000: off-=0x800000
            if 0x08000000+o+4+off==target: out.append(0x08000000+o)
    return out
if __name__=='__main__':
    t=int(sys.argv[1],16); n=int(sys.argv[2]) if len(sys.argv)>2 else 10
    for c in bl_callers(t):
        print('--',hex(c))
        for i in cs.disasm(r[c-0x08000000-2*n:c-0x08000000],c-2*n): print('   %x %s %s'%(i.address,i.mnemonic,i.op_str))
