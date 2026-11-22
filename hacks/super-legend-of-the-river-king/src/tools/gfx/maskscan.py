import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np, sys
from PIL import Image
rom=np.frombuffer(open(P.ROM,'rb').read(),dtype=np.uint8)
im=np.array(Image.open(sys.argv[1]).convert('RGB')).astype(int)
x0,y0,x1,y1=map(int,sys.argv[2:6])
white=(im[:,:,0]>200)&(im[:,:,1]>200)&(im[:,:,2]>200)
def masks(bpp,step):
    n=(len(rom)-8*bpp)//step; idx=np.arange(n)*step
    m=np.zeros((n,8),dtype=np.uint8)
    for k in range(bpp):
        m|=rom[idx[:,None]+(k//2)*16+np.arange(8)*2+(k%2)]
    return m,idx
for bpp,step in ((4,32),(2,16),(4,16)):
    m,idx=masks(bpp,step)
    keys={}
    for i,row in enumerate(map(bytes,m)):
        if sum(bin(b).count('1') for b in row)>=6: keys.setdefault(row,[]).append(int(idx[i]))
    for oy in range(8):
        for ox in range(8):
            for by in range(y0+oy,y1,8):
                for bx in range(x0+ox,x1,8):
                    blk=white[by:by+8,bx:bx+8]
                    if blk.sum()<6: continue
                    key=bytes(int(''.join('1' if v else '0' for v in r),2) for r in blk)
                    if key in keys: print(bpp,step,bx,by,[hex(o) for o in keys[key][:4]])
