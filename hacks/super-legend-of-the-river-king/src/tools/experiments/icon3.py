import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np, glob
from PIL import Image
A=_o.path.join(P.ROOT,'data','dumps')+'/'  # dumps renamed: VideoRamSign.dmp etc.
im=np.array(Image.open(_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_59.png')).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
for f in glob.glob(A+'*VideoRam*.dmp'):
    v=open(f,'rb').read()
    for bpp in (4,2):
        a=np.frombuffer(v,dtype=np.uint8).reshape(-1,8*bpp)
        T=np.zeros((a.shape[0],8,8),dtype=np.int32)
        for k in range(bpp):
            pl=a[:,(k//2)*16+np.arange(8)*2+(k%2)]
            T|=((pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1)<<k
        T=T.reshape(-1,64); oh=np.eye(16,dtype=np.int8)[T]; nz=(T!=0).sum(1)
        for by in range(112,126):
          for bx in range(34,60):
            c=cid[by:by+8,bx:bx+8].reshape(64); cols,inv=np.unique(c,return_inverse=True)
            if len(cols)<3: continue
            coh=np.eye(len(cols),dtype=np.int8)[inv]
            M=np.einsum('npi,pk->nik',oh,coh,dtype=np.int16)>0; M[:,0,:]=False
            ok=(M.sum(2)<=1).all(1)&(M.sum(1)<=1).all(1)&(nz>=20)&(M.any(2).sum(1)>=3)
            for n in np.nonzero(ok)[0]: print(f.split('VideoRam')[1],bpp,bx,by,hex(n*8*bpp))
