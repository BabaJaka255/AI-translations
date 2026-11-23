import sys; import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D, grid
rom=sys.argv[1]; st=sys.argv[2]; seq=sys.argv[3]; out=sys.argv[4]
d=D(rom, st); files=[]
# seq tokens: BTN:frames  (hold) ; w:frames ; s = shot
i=0
for tok in seq.split():
    k,_,v=tok.partition(':')
    if k=='s': f='ex%03d.png'%i; d.shot(f); files.append(f); i+=1
    elif k=='w': d.step(None,int(v))
    elif k=='save': d.save(v)
    else: d.step(k,int(v))
grid(files,out,cols=6)
