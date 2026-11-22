import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys; sys.path.insert(0,P.BUILD)
import numpy as np
from PIL import Image
rom=open(P.ROM,'rb').read()
im=np.array(Image.open(_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_59.png')).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
def tiles(d,bpp,step):
    out=[]
    for off in range(0,len(d)-8*bpp,step):
        pass
    n=(len(d)-8*bpp)//step
    idx=np.arange(n)*step
    a=np.frombuffer(d,dtype=np.uint8)
    T=np.zeros((n,8,8),dtype=np.int8)
    for k in range(bpp):
        pl=a[idx[:,None]+(k//2)*16+np.arange(8)*2+(k%2)]
        T|=(((pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1)<<k).astype(np.int8)
    return T.reshape(-1,64),idx
crops=[]
for by in range(112,126):
  for bx in range(34,60):
    c=cid[by:by+8,bx:bx+8].reshape(64)
    cols,inv=np.unique(c,return_inverse=True)
    if len(cols)>=3: crops.append((bx,by,inv,len(cols)))
for bpp,step in ((4,32),(2,16)):
  for start in range(0,len(rom),0x40000):
    T,idx=tiles(rom[start:start+0x40000+64],bpp,step)
    oh=np.eye(16,dtype=np.int8)[T]
    nz=(T!=0).sum(1)
    for bx,by,inv,K in crops:
        coh=np.eye(K,dtype=np.int8)[inv]
        M=np.einsum('npi,pk->nik',oh,coh,dtype=np.int16)>0; M[:,0,:]=False
        ok=(M.sum(2)<=1).all(1)&(M.sum(1)<=1).all(1)&(nz>=24)&(M.any(2).sum(1)>=3)
        for n in np.nonzero(ok)[0]: print(bpp,bx,by,hex(start+idx[n]))
