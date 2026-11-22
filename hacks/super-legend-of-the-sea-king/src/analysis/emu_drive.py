"""Drive snes9x headless: python drive.py rom outprefix 'SEQ'
SEQ = space separated: wait:N | press:BTN[:hold] | shot:name"""
import sys, numpy as np, stable_retro as retro
from PIL import Image
B=["B","Y","SELECT","START","UP","DOWN","LEFT","RIGHT","A","X","L","R"]
em=retro.RetroEmulator(sys.argv[1]); pre=sys.argv[2]
def step(mask=None,n=1):
    for _ in range(n):
        m=np.zeros(12,np.uint8)
        if mask: m[B.index(mask)]=1
        em.set_button_mask(m,0); em.step()
for tok in sys.argv[3].split():
    k,_,v=tok.partition(':')
    if k=='wait': step(None,int(v))
    elif k=='press':
        btn,_,h=v.partition(':'); step(btn,int(h or 4)); step(None,8)
    elif k=='shot': Image.fromarray(em.get_screen()).resize((512,448),Image.NEAREST).save(pre+v+'.png')
open(pre+'state.bin','wb').write(em.get_state())
