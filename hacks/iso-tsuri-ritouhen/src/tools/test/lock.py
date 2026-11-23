import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import numpy as np, stable_retro as retro
from s9x_state import blocks
from drive import B
rom,stp,N,tag=sys.argv[1],sys.argv[2],int(sys.argv[3]),sys.argv[4]
seq=sys.argv[5] if len(sys.argv)>5 else 'A:4'
e=retro.RetroEmulator(rom); e.set_state(open(stp,'rb').read())
def run(btn,n):
    m=np.zeros(12,np.uint8)
    if btn: m[B.index(btn)]=1
    for _ in range(n): e.set_button_mask(m,0); e.step()
for tok in seq.split():
    k,_,v=tok.partition(':'); run(None if k=='w' else k,int(v))
snaps=[]
for t in range(0,N,300):
    run(None,300); snaps.append(np.frombuffer(blocks(e.get_state())['RAM'],np.uint8))
np.save('lock_%s.npy'%tag,np.array(snaps))
from PIL import Image; Image.fromarray(e.get_screen()).save('lock_%s.png'%tag)
open('lock_%s.bin'%tag,'wb').write(e.get_state())
