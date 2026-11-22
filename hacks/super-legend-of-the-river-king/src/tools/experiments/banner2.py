import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle,struct; sys.path.insert(0,P.BUILD)
import numpy as np, lzss
from PIL import Image
rom=open(P.ROM,'rb').read()
shot=_o.path.join(_o.path.dirname(P.ROOT),'docs','images','screenshots','shot_55.png')
im=np.array(Image.open(shot).convert('RGB')).astype(np.int32)
cid=im[:,:,0]*65536+im[:,:,1]*256+im[:,:,2]
blocks=[k for k,_,_ in pickle.load(open('blocks.pkl','rb'))]+pickle.load(open('tbl.pkl','rb'))
for o in range(0x74E,0x7B6,4):
    a,b=struct.unpack('<HH',rom[o:o+4]); blocks.append((b,a))
blocks=sorted(set(blocks))
def tiles4(d):
    a=np.frombuffer(d[:len(d)//32*32],dtype=np.uint8).reshape(-1,32)
    out=np.zeros((a.shape[0],8,8),dtype=np.int32)
    for k in range(4):
        pl=a[:,(k//2)*16+np.arange(8)*2+(k%2)]
        bits=(pl[:,:,None]>>(7-np.arange(8))[None,None,:])&1
        out|=bits<<k
    return out.reshape(-1,64)
allt=[];src=[]
for b,a in blocks:
    try: d,_=lzss.decompress(rom,lzss.lo(b,a))
    except Exception: continue
    t=tiles4(d)
    for fl in (0,1):
        tt=t if not fl else t.reshape(-1,8,8)[:,:,::-1].reshape(-1,64)
        allt.append(tt); src+= [((b,a),i,fl) for i in range(len(tt))]
T=np.concatenate(allt); print('tiles',len(T))
oh=np.eye(16,dtype=np.int32)[T]  # N,64,16
res={}
for oy in range(8):
  for ox in range(8):
    for by in range(48+oy,88,8):
      for bx in range(152+ox,180,8):
        c=cid[by:by+8,bx:bx+8].reshape(64)
        cols,inv=np.unique(c,return_inverse=True)
        if len(cols)<3: continue
        coh=np.eye(len(cols),dtype=np.int32)[inv]   # 64,K
        M=np.einsum('npi,pk->nik',oh,coh)>0        # N,16,K
        M[:,0,:]=False
        idx_ok=(M.sum(2)<=1).all(1)
        col_ok=(M.sum(1)<=1).all(1)
        opaque=(T!=0).sum(1)
        nidx=(M.any(2)).sum(1)
        ok=idx_ok&col_ok&(opaque>=28)&(nidx>=3)
        for n in np.nonzero(ok)[0]:
            res.setdefault(src[n][0],set()).add((src[n][1],bx,by))
for k,v in sorted(res.items(),key=lambda x:-len(x[1]))[:8]: print('%02X:%04X'%k,len(v),sorted(v)[:10])
