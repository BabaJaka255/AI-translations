import sys,struct,os
def entries(d):
    out=[];i=0
    while i+32<=len(d):
        size,=struct.unpack_from('<I',d,i); name=d[i+4:i+28].split(b'\0')[0]; off,=struct.unpack_from('<I',d,i+28)
        if not name or not all(32<c<127 for c in name): break
        out.append((name.decode(),off,size)); i+=32
    return out
if __name__=='__main__':
    d=open(sys.argv[1],'rb').read(); E=entries(d)
    for n,o,s in E: print(f"{o:8x} {s:8d} {n}")
    if len(sys.argv)>2:
        os.makedirs(sys.argv[2],exist_ok=True)
        for n,o,s in E: open(os.path.join(sys.argv[2],n),'wb').write(d[o:o+s])
