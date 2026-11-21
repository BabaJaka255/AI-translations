import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np, sys
from PIL import Image
rom=np.frombuffer(open(P.ROM,'rb').read(),dtype=np.uint8)
im=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
x0,y0,x1,y1=map(int,sys.argv[2:6])
white=(im[:,:,0]>200)&(im[:,:,1]>200)&(im[:,:,2]>200)
crops={}
for oy in range(8):
    for ox in range(8):
        for by in range(y0+oy,y1,8):
            for bx in range(x0+ox,x1,8):
                blk=white[by:by+8,bx:bx+8]
                if blk.sum()<8 or blk.sum()>40: continue
                key=bytes(int(''.join('1' if v else '0' for v in r),2) for r in blk)
                crops.setdefault(key,[]).append((bx,by))
n=len(rom)-32
for step in (16,):
    idx=np.arange(0,n,step)
    p=[rom[idx[:,None]+np.arange(8)*2+k] for k in range(2)]
    for name,m in (('p0',p[0]),('p1',p[1]),('p0&p1',p[0]&p[1])):
        mb=[bytes(r) for r in m]
        for i,key in enumerate(mb):
            if key in crops: print(name,hex(int(idx[i])),crops[key][:3])
