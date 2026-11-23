import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D
rom=sys.argv[1]; st=sys.argv[2] if sys.argv[2]!='-' else None
d=D(rom, st)
def press(b,n=1):
    for _ in range(n): d.step(b,10); d.step(None,12)
for tok in sys.argv[3].split():
    k,_,v=tok.partition(':')
    if k=='w': d.step(None,int(v))
    elif k=='shot': d.shot(v)
    elif k=='save': d.save(v)
    else: press(k, int(v) if v else 1)
