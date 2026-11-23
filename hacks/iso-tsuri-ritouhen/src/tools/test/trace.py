import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, stable_retro as retro
from s9x_state import blocks
from drive import B
rom,stp,pat,N=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4])
e=retro.RetroEmulator(rom); e.set_state(open(stp,'rb').read())
def mask(bs):
    m=np.zeros(12,np.uint8)
    for b in bs.split('+'):
        if b: m[B.index(b)]=1
    return m
toks=[(t.partition(':')[0], int(t.partition(':')[2])) for t in pat.split()]
W=lambda w,a: w[a]|w[a+1]<<8
t=0; last=None
while t<N:
    for b,n in toks:
        for _ in range(n):
            e.set_button_mask(mask('' if b=='w' else b),0); e.step(); t+=1
            if t%5==0:
                w=blocks(e.get_state())['RAM']
                v=tuple(W(w,a) for a in (0x7EF,0x752,0x7CB,0x700,0x702,0x7F1,0x7F3,0x7D1))
                if v!=last: print(t, 'EF=%x 52=%x CB=%x 700=%x 702=%x F1=%x F3=%x D1=%x'%v, 'bait %x,%x'%(W(w,0x758),W(w,0x75A)), 'fish %x,%x'%(W(w,0x7F5),W(w,0x7F7))); last=v
