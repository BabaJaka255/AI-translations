import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD); sys.path.insert(0,'.')
import lzss,struct
from match import tiles_of, canon
rom=open(P.ROM,'rb').read()
SETS=[(0x21,0xFAF7),(0x22,0xE0AF),(0x23,0xCE21),(0x24,0xBDBB),(0x25,0xA381),(0x26,0x91D1),(0x26,0xF1EA),(0x27,0xC31F)]
d0,_=lzss.decompress(rom,lzss.lo(0x21,0xFAF7)); T0=tiles_of(d0)
def edge_sig(t,part):
    # frame signature: TL uses rows0-1 + col0 ; TR rows0-1 + col7 ; BL rows14-15 (=rows 6-7) + col0 ; BR rows6-7+col7
    if part=='TL': px=[t[i] for i in range(16)]+[t[y*8] for y in range(8)]
    if part=='TR': px=[t[i] for i in range(16)]+[t[y*8+7] for y in range(8)]
    if part=='BL': px=[t[48+i] for i in range(16)]+[t[y*8] for y in range(8)]
    if part=='BR': px=[t[48+i] for i in range(16)]+[t[y*8+7] for y in range(8)]
    return canon(px)
REF={'TL':edge_sig(T0[0x21e],'TL'),'TR':edge_sig(T0[0x21f],'TR'),'BL':edge_sig(T0[0x22c],'BL'),'BR':edge_sig(T0[0x22d],'BR')}
def find(T):
    return {p:[i for i,t in enumerate(T) if edge_sig(t,p)==REF[p]] for p in REF}
if __name__=='__main__':
    for b,a in SETS:
        d,_=lzss.decompress(rom,lzss.lo(b,a)); T=tiles_of(d)
        f=find(T); print('%02X:%04X'%(b,a),{k:[hex(x) for x in v] for k,v in f.items()})
