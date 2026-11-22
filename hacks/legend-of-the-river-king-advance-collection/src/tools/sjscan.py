import sys
d=open(sys.argv[1],'rb').read()
i=0;out=[]
while i<len(d)-1:
    j=i;s=''
    while j<len(d)-1:
        b=d[j]
        if (0x81<=b<=0x9f or 0xe0<=b<=0xea) and 0x40<=d[j+1]<=0xfc and d[j+1]!=0x7f:
            try: s+=d[j:j+2].decode('cp932'); j+=2; continue
            except: break
        break
    if len(s)>=4: out.append((i,s)); i=j
    else: i+=1
for a,s in out: print(hex(a),s)
