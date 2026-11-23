import sys, random; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, stable_retro as retro
from s9x_state import blocks
from drive import B
from PIL import Image
rom,stp,N,seed,tag=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
e=retro.RetroEmulator(rom); e.set_state(open(stp,'rb').read())
rng=random.Random(seed); t=0; snaps=[]; ts=[]
names=['A','B','Y','X','L','R','UP','DOWN','LEFT','RIGHT']
def mask(btns):
    m=np.zeros(12,np.uint8)
    for b in btns: m[B.index(b)]=1
    return m
while t<N:
    btns=rng.sample(names, rng.choice([0,0,1,1,1,2])); n=rng.randint(4,90)
    for _ in range(n): e.set_button_mask(mask(btns),0); e.step(); t+=1
    snaps.append(np.frombuffer(blocks(e.get_state())['RAM'],np.uint8)); ts.append(t)
    if t//1500!=(t-n)//1500: Image.fromarray(e.get_screen()).save('fz_%s_%d_%06d.png'%(tag,seed,t))
np.savez_compressed('fz_%s_%d.npz'%(tag,seed),s=np.array(snaps),t=np.array(ts))
