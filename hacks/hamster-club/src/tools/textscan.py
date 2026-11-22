"""Find Japanese text outside the event script by scoring byte bigrams against
the dumped script. Usage (game folder): python3 tools/textscan.py 10 -3.1 > notes/text-candidates.txt
Prints offset, length, bank and a decoded preview. Banks >= 0x12 are graphics noise."""
import sys, math, collections, os
sys.path.insert(0, 'tools'); sys.path.insert(0, os.environ.get('RHTK', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'toolkit')))
import hcscript as H
from rhtk.table import Table
rom=open('rom/original.gbc','rb').read(); t=Table.load('tables/jp.tbl')
ops,entries,_=H.walk(rom,[(0xb,0x2F5FD)])
cov=bytearray(len(rom))
msgs=list(H.messages(rom,ops))
for o,op in ops.items(): cov[o:o+op.size]=b'\1'*op.size
big=collections.Counter(); uni=collections.Counter()
for s,e in msgs:
    d=bytes(b for b in rom[s:e] if b not in (0,0xEE,0xEF,0xF0))
    for a,b in zip(d,d[1:]): big[(a,b)]+=1
    for a in d: uni[a]+=1
def lp(a,b):
    if a in (0,0xA3) and b in (0,0xA3): return -4.5
    if a == b: return -4.0
    if a in (0,0xA3) or b in (0,0xA3): return -3.0
    return math.log((big[(a,b)]+0.05)/(uni[a]+12.8))
n=len(rom); W=int(sys.argv[1]); th=float(sys.argv[2])
pref=[0.0]
for k in range(n-1): pref.append(pref[-1]+lp(rom[k],rom[k+1]))
if len(sys.argv)>3:
    import random
    vals=[(pref[s+W]-pref[s])/W for s,e in msgs if e-s>W]
    vals.sort(); print('text p10',vals[len(vals)//10],'p50',vals[len(vals)//2])
    r=[(pref[k+W]-pref[k])/W for k in random.sample(range(0x40000,n-W),5000)]
    r.sort(); print('rand p50',r[2500],'p99',r[4950],'p999',r[4995]); sys.exit()
segs=[];k=0
while k<n-W:
    if cov[k]: k+=1; continue
    if (pref[k+W]-pref[k])/W>th:
        s=k
        while k<n-W and not cov[k] and (pref[k+W]-pref[k])/W>th: k+=1
        segs.append((s,k+W))
    k+=1
m=[]
for s,e in segs:
    if m and s-m[-1][1]<=8: m[-1][1]=e
    else: m.append([s,e])
tot=0
for s,e in m:
    if len(set(rom[s:e]))<8: continue
    tot+=e-s
    print(f"{s:06X} {e-s:5d} b{s//0x4000:02X}  "+t.decode(rom[:e],s,stop_at_end=False)[0].replace('\n','')[:200])
print('total',tot,len(m))
