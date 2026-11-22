import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import numpy as np, lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
shot,b,a,X0,X1,Y0,Y1=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3],16),*map(int,sys.argv[4:8])
d=lzss.decompress(rom,lzss.lo(b,a))[0]
im=np.array(Image.open(shot).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
A=np.frombuffer(d,dtype=np.uint8).reshape(-1,32)
T=np.zeros((A.shape[0],8,8),dtype=np.int32)
for k in range(4):
    pl=A[:,(k//2)*16+np.arange(8)*2+(k%2)]
    T|=((pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1)<<k
T=T.reshape(-1,64)
oh=np.eye(16,dtype=np.int32)[T]
red=(im[:,:,0]>180)&(im[:,:,1]<90)
ys,xs=np.nonzero(red); sel=(xs>=X0)&(xs<=X1)&(ys>=Y0)&(ys<=Y1)
x0,x1,y0,y1=xs[sel].min(),xs[sel].max(),ys[sel].min(),ys[sel].max(); print('bbox',x0,x1,y0,y1)
for by in range(y0-7,y1+1):
  for bx in range(x0-7,x1+1):
    c=cid[by:by+8,bx:bx+8].reshape(64)
    cols,inv=np.unique(c,return_inverse=True)
    coh=np.eye(len(cols),dtype=np.int32)[inv]
    M=np.einsum('npi,pk->nik',oh,coh)>0; M[:,0,:]=False
    ok=(M.sum(2)<=1).all(1)&(M.sum(1)<=1).all(1)&((T!=0).sum(1)>=20)&(M.any(2).sum(1)>=3)
    for n in np.nonzero(ok)[0]: print(bx,by,hex(n))
