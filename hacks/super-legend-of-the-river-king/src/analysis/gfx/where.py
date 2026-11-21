import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,'.')
from match import *
shot=sys.argv[1]; b,a=int(sys.argv[2],16),int(sys.argv[3],16); ox,oy=int(sys.argv[4]),int(sys.argv[5])
x0,y0,x1,y1=map(int,sys.argv[6:10])
d,_=lzss.decompress(rom,lzss.lo(b,a)); T=tiles_of(d); H=index(T)
sb=screen_blocks(shot,ox,oy)
for by in range(oy,240,8):
    if by<y0 or by>y1: continue
    row=[]
    for bx in range(ox,256,8):
        if bx<x0 or bx>x1: continue
        v=sb.get((bx,by)); m=H.get(v,[])
        row.append(('%03x'%m[0][0]+('f' if m[0][1] else ' ')) if m else ' -- ')
    print('%3d '%by+' '.join(row))
