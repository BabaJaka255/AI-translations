import sys as _s, os as _o; _s.path.insert(0,_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'..' if _o.path.basename(_o.path.dirname(_o.path.abspath(__file__)))=='analysis' else '../..','build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys,pickle
start=int(sys.argv[1]); chars=sys.argv[2]
use,ctx,low=pickle.load(open(P.data('usage.pkl'),'rb'))
low=sorted(low,key=lambda t:-t[1])
batch=low[start:start+len(chars)]
assert len(batch)==len(chars),(len(batch),len(chars))
with open(P.b('kanji_overrides.txt'),'a',encoding='utf-8') as f:
    for (g,c,v),ch in zip(batch,chars): f.write("%X=%s\n"%(g,ch))
print("applied",len(chars))
