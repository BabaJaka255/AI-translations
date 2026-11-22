"""setstr.py FILE_WITH 'id|text' lines  -> replaces those ids in text/en_*.txt"""
import sys,re,glob
rep={}
for l in open(sys.argv[1],encoding='utf-8'):
    l=l.rstrip('\n')
    if not l or l.startswith('#'): continue
    i,t=l.split('|',1); rep[int(i)]=t
done=set()
for f in sorted(glob.glob('text/en_*.txt')):
    L=open(f,encoding='utf-8').read().split('\n'); ch=False
    for k,l in enumerate(L):
        m=re.match(r'(\d+)\|',l)
        if m and int(m.group(1)) in rep:
            L[k]='%s|%s'%(m.group(1),rep[int(m.group(1))]); ch=True; done.add(int(m.group(1)))
    if ch: open(f,'w',encoding='utf-8').write('\n'.join(L))
print('set',len(done),'missing',sorted(set(rep)-done))
