import sys
d=open(sys.argv[1],'rb').read()
goj='あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん'
sj=''.join(chr(c) for c in range(ord('ぁ'),ord('ん')+1))
def kat2hir(s): return ''.join(chr(ord(c)-0x60) if 'ァ'<=c<='ン' else c for c in s)
orders={'goj':goj,'sjis':sj,'goj_yu':'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもや ゆ よらりるれろわ  をん'}
words=sys.argv[2:]
for w in words:
    h=kat2hir(w)
    for on,o in orders.items():
        if not all(c in o for c in h): continue
        idx=[o.index(c) for c in h]
        diffs=[idx[k+1]-idx[k] for k in range(len(idx)-1)]
        for width in (1,2):
            n=len(idx)
            hits=[]
            for i in range(0,len(d)-n*width):
                if width==1:
                    v=[d[i+k] for k in range(n)]
                else:
                    if i%2: continue
                    v=[d[i+2*k]|d[i+2*k+1]<<8 for k in range(n)]
                ok=all(v[k+1]-v[k]==diffs[k] for k in range(n-1))
                if ok: hits.append((i,v[0]-idx[0]))
            from collections import Counter
            c=Counter(b for a,b in hits)
            print(w,on,width,len(hits),c.most_common(5), [hex(a) for a,b in hits[:6]])
