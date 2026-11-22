import struct,sys
rom=open('../rom/k34.gba','rb').read()
N=0x231700
def plaus(t):
    n=0;kana=0
    i=t
    while i<N and n<300:
        b=rom[i]
        if b==0xf0: break
        if 0x24<=b<=0x96: kana+=1
        elif b>=0xd0 and b not in (0xf1,0xf2,0xf5,0xf6,0xf8,0xf9,0xfb,0xff,0xfa,0xf3,0xf4,0xf7,0xfc,0xfd,0xfe): return 0
        i+=1;n+=1
    else: return 0
    if n==0: return 0
    return kana if kana>=2 and kana>=n*0.5 else 0
hits=[]
for o in range(0,N,4):
    v=struct.unpack_from('<I',rom,o)[0]
    if 0x08000000<=v<0x08000000+N:
        k=plaus(v-0x08000000)
        if k: hits.append((o,v-0x08000000,k))
# cluster contiguous tables
tables=[];cur=[]
for h in hits:
    if cur and h[0]-cur[-1][0]>8:
        tables.append(cur);cur=[]
    cur.append(h)
if cur: tables.append(cur)
for t in tables:
    if len(t)>=1:
        print(hex(t[0][0]),hex(t[-1][0]),len(t),'targets',hex(min(x[1] for x in t)),hex(max(x[1] for x in t)))
