import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D
d=D(sys.argv[1], sys.argv[2])
for tok in sys.argv[3].split():
    k,_,v=tok.partition(':')
    if k=='shot': d.shot(v)
    elif k=='save': d.save(v)
    elif k=='w': d.step(None,int(v))
    else: d.step(k,int(v))
