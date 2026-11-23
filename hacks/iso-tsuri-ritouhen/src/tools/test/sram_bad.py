import sys, re; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D, grid
def blocks(d):
    out={}; i=d.index(b'\n')+1
    while i<len(d):
        m=re.match(rb'([A-Z]{3}):(\d{6}):',d[i:i+11])
        if not m: break
        n=int(m.group(2)); out[m.group(1).decode()]=(i+11,n); i+=11+n
    return out
src=bytearray(open('t/p_fish.bin','rb').read()); o,n=blocks(bytes(src))['SRA']
for k in range(0x40, 0x200): src[o+k]^=0x5A
d=D(sys.argv[1]); d.step(None,1); st=bytearray(d.em.get_state()); o2,n2=blocks(bytes(st))['SRA']
st[o2:o2+n]=src[o:o+n]; d.em.set_state(bytes(st))
fs=[]
for i in range(6):
    d.step(None,150); f='t/x%d.png'%i; d.shot(f); fs.append(f)
d.step('START',10)
for i in range(6,9):
    d.step(None,100); f='t/x%d.png'%i; d.shot(f); fs.append(f)
grid(fs,'t/g.png',3)
