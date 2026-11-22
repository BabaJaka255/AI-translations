import sys,struct
from capstone import *
rom=open('../rom/k34.gba','rb').read()
md=Cs(CS_ARCH_ARM,CS_MODE_THUMB)
def dis(a,n):
    end=a+n; out=[]
    while a<end:
        o=a-0x08000000
        ins=list(md.disasm(rom[o:o+4],a,count=1))
        if not ins:
            out.append('%08x: .hword 0x%04x'%(a,struct.unpack_from('<H',rom,o)[0])); a+=2; continue
        i=ins[0]
        s='%08x: %-8s %s'%(i.address,i.mnemonic,i.op_str)
        if i.mnemonic.startswith('ldr') and '[pc,' in i.op_str:
            off=int(i.op_str.split('#')[-1].rstrip(']'),16)
            la=((a+4)&~3)+off
            s+='   ; =0x%08x'%struct.unpack_from('<I',rom,la-0x08000000)[0]
        out.append(s); a+=i.size
    return out
if __name__=='__main__':
    print('\n'.join(dis(int(sys.argv[1],16),int(sys.argv[2],16))))
