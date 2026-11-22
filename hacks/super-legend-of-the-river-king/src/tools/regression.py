import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,struct,json
sys.path.insert(0,P.BUILD)
from sim import *

def apply_ips(rom,ips):
    r=bytearray(rom); i=5
    while ips[i:i+3]!=b'EOF':
        o=int.from_bytes(ips[i:i+3],'big'); n=int.from_bytes(ips[i+3:i+5],'big'); i+=5
        if n==0:
            n=int.from_bytes(ips[i:i+2],'big'); v=ips[i+2]; i+=3
            if o+n>len(r): r+=bytes(o+n-len(r))
            r[o:o+n]=bytes([v])*n
        else:
            if o+n>len(r): r+=bytes(o+n-len(r))
            r[o:o+n]=ips[i:i+n]; i+=n
    return r
orig=open(ROM,'rb').read()
old=apply_ips(orig,open(P.REG_IPS,'rb').read())
new=bytearray(open(P.out('knt2_en.sfc'),'rb').read())
# string table pointers
import knt2lib
ptrs=[struct.unpack('<H',orig[knt2lib.TABLE_OFF+2*i:knt2lib.TABLE_OFF+2*i+2])[0] for i in range(knt2lib.TABLE_N)]
seen=set(); diffs=0; n=0; errs=0
for i,p in enumerate(ptrs):
    if p in seen: continue
    seen.add(p)
    imgs=[]
    for rom in (old,new):
        try:
            c=make_cpu(bytes(rom))
            run_dialog(c,p,5)
            imgs.append(render_stage(c,rows=2).tobytes())
        except Exception as e:
            imgs.append(None); errs+=1
    n+=1
    if imgs[0] is None or imgs[1] is None or imgs[0]!=imgs[1]:
        diffs+=1; print('diff id',i,hex(p), 'err' if imgs[0] is None or imgs[1] is None else '')
print('checked',n,'diffs',diffs,'errs',errs)
