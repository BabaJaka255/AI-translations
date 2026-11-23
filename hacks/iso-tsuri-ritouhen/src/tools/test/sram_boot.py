import sys, re; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D
def blocks(d):
    out={}; i=d.index(b'\n')+1
    while i<len(d):
        m=re.match(rb'([A-Z]{3}):(\d{6}):',d[i:i+11])
        if not m: break
        n=int(m.group(2)); out[m.group(1).decode()]=(i+11,n); i+=11+n
    return out
src=open(sys.argv[2],'rb').read()
d=D(sys.argv[1]); d.step(None,1); st=bytearray(d.em.get_state())
bs, bd = blocks(src), blocks(bytes(st))
print(sorted(bd))
o,n=bs['SRA']; o2,n2=bd['SRA']; assert n==n2
st[o2:o2+n]=src[o:o+n]; d.em.set_state(bytes(st))
d.step(None,600); d.step('START',10); d.step(None,150); d.shot(sys.argv[3]); d.save(sys.argv[3]+'.bin')
