"""Re-wrap dialogue strings whose lines are too long. Keeps a break after . ! ? and after
short lines that stand alone (names, exclamations). Usage: python3 build/reflow.py [width]"""
import sys,re,glob,json
sys.path.insert(0,'build')
import translations as T
from umilib import WID
W=int(sys.argv[1]) if len(sys.argv)>1 else 22
def cols(l): return len(re.sub(r'\{..\}','',l))+sum(WID.get(m,12) for m in re.findall(r'\{(..)\}',l))
def reflow(t):
    paras=[]; cur=[]
    for l in t.split('\n'):
        if cur and cur[-1].endswith('-'): cur[-1]=cur[-1][:-1]+l; continue
        cur.append(l)
        if l.strip()=='' or (len(cur)==1 and cols(l)<=12 and re.search(r'[.!?]$',l)): paras.append(cur); cur=[]
    if cur: paras.append(cur)
    out=[]
    for p in paras:
        lead=re.match(r'^ *',p[0]).group(0)
        words=' '.join(x.strip() for x in p).split(' ')
        line=lead
        for w in words:
            cand=(line+' '+w) if line.strip() else lead+w
            if cols(cand)<=W: line=cand
            else: out.append(line); line=lead+w
        out.append(line)
    return '\n'.join(out)
changed={}
FORCE=set(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else set()
for sid,t in sorted(T.EN.items()):
    if sid in T.FIXED or sid in T.WIDE or sid in T.TIPS: continue
    if any(cols(l)>W for l in t.split('\n')) or sid in FORCE: changed[sid]=reflow(t)
for f in glob.glob('build/tr_*.py'):
    src=open(f).read(); n=src
    for sid,new in changed.items():
        m=re.search(r'^%d:(".*?(?<!\\)"),$'%sid,n,re.M)
        if m: n=n[:m.start(1)]+json.dumps(new)+n[m.end(1):]
    if n!=src: open(f,'w').write(n)
for sid,new in changed.items(): print(sid,repr(T.EN[sid]),'\n   ->',repr(new))
print(len(changed),'reflowed')
