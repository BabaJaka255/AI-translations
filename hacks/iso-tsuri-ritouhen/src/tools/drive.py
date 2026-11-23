import sys, numpy as np, stable_retro as retro
from PIL import Image
B=["B","Y","SELECT","START","UP","DOWN","LEFT","RIGHT","A","X","L","R"]
class D:
    def __init__(s, rom='iso.sfc', state=None):
        s.em=retro.RetroEmulator(rom)
        if state: s.em.set_state(open(state,'rb').read())
    def step(s,btn=None,n=1):
        for _ in range(n):
            m=np.zeros(12,np.uint8)
            if btn:
                for b in btn.split('+'): m[B.index(b)]=1
            s.em.set_button_mask(m,0); s.em.step()
    def press(s,btn,hold=3,after=10): s.step(btn,hold); s.step(None,after)
    def shot(s,name): Image.fromarray(s.em.get_screen()).save(name)
    def save(s,name): open(name,'wb').write(s.em.get_state())
    def seq(s,txt):
        for tok in txt.split():
            k,_,v=tok.partition(':')
            if k=='w': s.step(None,int(v))
            elif k=='shot': s.shot(v)
            elif k=='save': s.save(v)
            else:
                n=int(v) if v else 1
                for _ in range(n): s.press(k)
def grid(files,out,cols=4):
    ims=[Image.open(f) for f in files]; w,h=ims[0].size
    rows=(len(ims)+cols-1)//cols; W=Image.new('RGB',(w*cols,h*rows))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*w,(i//cols)*h))
    W.save(out)
