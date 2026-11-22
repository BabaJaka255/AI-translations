"""Headless snes9x driver (stable-retro).
python3 emu.py ROM OUTPREFIX 'SEQ' [STATE_IN]
SEQ tokens: wait:N | press:BTN[:hold] | hold:BTN:N | shot:name | grid:name (accumulate shots) | ram:name (dump WRAM)
Writes OUTPREFIX+'state.bin' at the end."""
import sys, numpy as np, stable_retro as retro
from PIL import Image
B=["B","Y","SELECT","START","UP","DOWN","LEFT","RIGHT","A","X","L","R"]
em=retro.RetroEmulator(sys.argv[1]); pre=sys.argv[2]
if len(sys.argv)>4: em.set_state(open(sys.argv[4],'rb').read())
def step(btn=None,n=1):
    for _ in range(n):
        m=np.zeros(12,np.uint8)
        if btn: m[B.index(btn)]=1
        em.set_button_mask(m,0); em.step()
shots=[]
for tok in sys.argv[3].split():
    k,_,v=tok.partition(':')
    if k=='wait': step(None,int(v))
    elif k=='press':
        btn,_,h=v.partition(':'); step(btn,int(h or 4)); step(None,8)
    elif k=='hold':
        btn,_,h=v.partition(':'); step(btn,int(h))
    elif k=='shot':
        im=Image.fromarray(em.get_screen()); shots.append(im); im.resize((512,448),Image.NEAREST).save(pre+v+'.png')
    elif k=='ram':
        open(pre+v+'.wram','wb').write(bytes(em.get_memory_data('ram') if hasattr(em,'get_memory_data') else b''))
if shots:
    w,h=shots[0].size; c=min(4,len(shots)); r=(len(shots)+c-1)//c
    G=Image.new('RGB',(w*c,h*r))
    for i,s in enumerate(shots): G.paste(s,((i%c)*w,(i//c)*h))
    G.resize((w*c*3//2,h*r*3//2),Image.NEAREST).save(pre+'grid.png')
open(pre+'state.bin','wb').write(em.get_state())
