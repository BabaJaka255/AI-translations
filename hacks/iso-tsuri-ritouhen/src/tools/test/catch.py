import sys, re; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D, grid
rom=bytearray(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'iso_en.sfc'),'rb').read())
assert rom[0x9F6D:0x9F71]==bytes.fromhex('20849fb0'); rom[0x9F6D:0x9F72]=bytes.fromhex('20aa9b3860')
open('t/test_catch.sfc','wb').write(rom)
def blocks(d):
    out={}; i=d.index(b'\n')+1
    while i<len(d):
        m=re.match(rb'([A-Z]{3}):(\d{6}):',d[i:i+11])
        if not m: break
        n=int(m.group(2)); out[m.group(1).decode()]=(i+11,n); i+=11+n
    return out
st=bytearray(open('t/p_fish.bin','rb').read()); o,n=blocks(bytes(st))['RAM']
fish=int(sys.argv[1]); size=int(sys.argv[2])
for a,v in ((0x7F1,1),(0x7F2,0),(0x7E9,fish),(0x7EA,0),(0x7EB,size),(0x7EC,0),(0x443,int(sys.argv[4]) if len(sys.argv)>4 else 3),(0x444,0)):
    st[o+a]=v
d=D('t/test_catch.sfc'); d.em.set_state(bytes(st)); d.step('A',4)
files=[]
for i in range(int(sys.argv[3]) if len(sys.argv)>3 else 8):
    d.step(None,120); f='t/c%d.png'%i; d.shot(f); files.append(f)
grid(files,'t/cgrid.png',4)
