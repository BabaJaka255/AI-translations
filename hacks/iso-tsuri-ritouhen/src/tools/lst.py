import d65,sys
r=open('iso.sfc','rb').read()
def listing(start,end,m=False,x=False,bank=0x80):
    out=[];o=start
    while o<end:
        op=r[o]
        n,md=d65.ops.get(op,('???','i'))
        ln=d65.LEN.get(md) or ((2 if m else 3) if md=='M' else (2 if x else 3))
        line=d65.disasm(r,o,1,m,x)[0]
        line='%02X:%04X'%(bank,o&0xffff)+line[7:]
        out.append(line)
        if op==0xC2: v=r[o+1]; m=m and not v&0x20; x=x and not v&0x10
        if op==0xE2: v=r[o+1]; m=m or bool(v&0x20); x=x or bool(v&0x10)
        o+=ln
    return out
if __name__=='__main__':
    s=int(sys.argv[1],16); e=int(sys.argv[2],16)
    print('\n'.join(listing(s,e)))
