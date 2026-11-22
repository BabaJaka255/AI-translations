import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import numpy as np
from PIL import Image
A=_o.path.join(P.ROOT,'data','dumps')+'/'  # dumps renamed: VideoRamSign.dmp etc.
v=open(A+'VideoRamSign.dmp','rb').read()
im=np.array(Image.open(_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_58.png')).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
a=np.frombuffer(v,dtype=np.uint8).reshape(-1,32)
T=np.zeros((a.shape[0],8,8),dtype=np.int32)
for k in range(4):
    pl=a[:,(k//2)*16+np.arange(8)*2+(k%2)]
    T|=((pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1)<<k
T=T.reshape(-1,64)
TT=np.concatenate([T,T.reshape(-1,8,8)[:,:,::-1].reshape(-1,64)])
oh=np.eye(16,dtype=np.int32)[TT]
# banner location: find red bbox
red=(im[:,:,0]>180)&(im[:,:,1]<90)
ys,xs=np.nonzero(red[:, :]); 
sel=(xs>140)&(xs<200)&(ys<120)
print('bbox',xs[sel].min(),xs[sel].max(),ys[sel].min(),ys[sel].max())
x0,x1,y0,y1=xs[sel].min(),xs[sel].max(),ys[sel].min(),ys[sel].max()
hits=[]
for by in range(y0-7,y1+1):
  for bx in range(x0-7,x1+1):
    c=cid[by:by+8,bx:bx+8].reshape(64)
    cols,inv=np.unique(c,return_inverse=True)
    coh=np.eye(len(cols),dtype=np.int32)[inv]
    M=np.einsum('npi,pk->nik',oh,coh)>0
    M[:,0,:]=False
    ok=(M.sum(2)<=1).all(1)&(M.sum(1)<=1).all(1)&((TT!=0).sum(1)>=20)&(M.any(2).sum(1)>=3)
    for n in np.nonzero(ok)[0]: hits.append((bx,by,n%len(T),n>=len(T)))
for h in hits: print(h, 'vram byte %05X'%( (h[2])*32))
