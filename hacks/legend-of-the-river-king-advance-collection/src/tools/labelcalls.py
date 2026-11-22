import struct
from capstone import *
from findbl import bl_callers, r
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB); cs.detail=False
def calls():
    res=[]
    for c in bl_callers(0x08039b50):
        ins=list(cs.disasm(r[c-0x08000000-24:c-0x08000000],c-24))
        regs={}
        for i in ins:
            m,op=i.mnemonic,i.op_str
            ops=[x.strip() for x in op.split(',')]
            if m=='movs' and ops[1].startswith('#'): regs[ops[0]]=('imm',int(ops[1][1:],0),i.address)
            elif m=='ldr' and 'pc' in op:
                off=int(ops[2].rstrip(']').strip('#'),0) if len(ops)>2 else 0
                la=((i.address+4)&~3)+off
                regs[ops[0]]=('lit',struct.unpack_from('<I',r,la-0x08000000)[0],la)
            elif m=='lsls' and ops[0] in regs and regs[ops[0]][0]=='imm' and ops[0]==ops[1]:
                regs[ops[0]]=('imm',regs[ops[0]][1]<<int(ops[2][1:],0),regs[ops[0]][2],'shift')
            else:
                for rr in ops[:1]:
                    if rr in regs and m not in('cmp','str','strh','strb'): regs.pop(rr)
        res.append((c,regs.get('r0'),regs.get('r1'),regs.get('r2')))
    return res
if __name__=='__main__':
    for c,a,b,d in calls():
        f=lambda x: None if x is None else (x[0],hex(x[1]),hex(x[2]))
        print(hex(c),f(a),f(b),f(d))
