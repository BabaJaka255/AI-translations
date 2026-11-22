import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
def tiles_of(d):
    out=[]
    for t in range(len(d)//32):
        b=t*32
        out.append(tuple(sum(((d[b+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for y in range(8) for x in range(8)))
    return out
def canon(seq):
    m={}; return tuple(m.setdefault(v,len(m)) for v in seq)
def index(tiles):
    h={}
    for i,t in enumerate(tiles):
        for flip in range(4):
            s=t
            if flip&1: s=tuple(s[y*8+7-x] for y in range(8) for x in range(8))
            if flip&2: s=tuple(s[(7-y)*8+x] for y in range(8) for x in range(8))
            h.setdefault(canon(s),[]).append((i,flip))
    return h
def screen_blocks(path,ox,oy):
    im=Image.open(path).convert('RGB'); px=im.load(); W,H=im.size
    res={}
    for by in range(oy,H-7,8):
        for bx in range(ox,W-7,8):
            res[(bx,by)]=canon(tuple(px[bx+x,by+y] for y in range(8) for x in range(8)))
    return res
if __name__=='__main__':
    shot=sys.argv[1]; b,a=int(sys.argv[2],16),int(sys.argv[3],16)
    d,_=lzss.decompress(rom,lzss.lo(b,a)); T=tiles_of(d); H=index(T)
    best=None
    for oy in range(8):
        for ox in range(8):
            sb=screen_blocks(shot,ox,oy)
            n=sum(1 for v in sb.values() if v in H and len(set(v))>2)
            if not best or n>best[0]: best=(n,ox,oy)
    print('align',best, 'of', len(sb))
