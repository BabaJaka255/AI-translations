import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle; sys.path.insert(0,P.BUILD)
import numpy as np, lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
im=np.array(Image.open(_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_59.png')).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
blocks=[k for k,_,_ in pickle.load(open('blocks.pkl','rb'))]
tb=pickle.load(open('tbl.pkl','rb'))
blocks+= [k for k in tb if k[0] not in (0x0D,0x0E,0x0F,0x10,0x11,0x12,0x13) and not (0x14<=k[0]<=0x1C)]
def tiles(d,bpp):
    n=len(d)//(8*bpp); a=np.frombuffer(d[:n*8*bpp],dtype=np.uint8).reshape(n,8*bpp)
    T=np.zeros((n,8,8),dtype=np.int32)
    for k in range(bpp):
        pl=a[:,(k//2)*16+np.arange(8)*2+(k%2)]
        T|=((pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1)<<k
    return T.reshape(-1,64)
allT=[];src=[]
for b,a in sorted(set(blocks)):
    d,_=lzss.decompress(rom,lzss.lo(b,a))
    for bpp in (2,4):
        t=tiles(d,bpp); allT.append(t); src+=[((b,a),bpp,i) for i in range(len(t))]
T=np.concatenate(allT); print(len(T))
oh=np.eye(16,dtype=np.int8)[T]
for by in range(112,126):
  for bx in range(34,60):
    c=cid[by:by+8,bx:bx+8].reshape(64)
    cols,inv=np.unique(c,return_inverse=True)
    if len(cols)<3: continue
    coh=np.eye(len(cols),dtype=np.int8)[inv]
    M=np.einsum('npi,pk->nik',oh,coh,dtype=np.int32)>0; M[:,0,:]=False
    ok=(M.sum(2)<=1).all(1)&(M.sum(1)<=1).all(1)&((T!=0).sum(1)>=24)&(M.any(2).sum(1)>=3)
    for n in np.nonzero(ok)[0]: print(bx,by,src[n])
