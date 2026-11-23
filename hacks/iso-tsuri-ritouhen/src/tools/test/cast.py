import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, stable_retro as retro
from s9x_state import blocks
from drive import B
rom,stp=sys.argv[1],sys.argv[2]
e=retro.RetroEmulator(rom); base=open(stp,'rb').read()
def mask(bs):
    m=np.zeros(12,np.uint8)
    for b in bs.split('+'):
        if b: m[B.index(b)]=1
    return m
def ram(): return blocks(e.get_state())['RAM']
for pat in sys.argv[3:]:
    e.set_state(base)
    for tok in pat.split():
        k,_,v=tok.partition(':')
        for _ in range(int(v)): e.set_button_mask(mask('' if k=='w' else k),0); e.step()
    w=ram()
    fish=[(w[0xFEB+4*i],w[0xFEC+4*i]) for i in range(32) if w[0xFEC+4*i]]
    print('%-40s hook x=%02x y=%02x  fish %s'%(pat, w[0x61C], w[0x61E], fish))
