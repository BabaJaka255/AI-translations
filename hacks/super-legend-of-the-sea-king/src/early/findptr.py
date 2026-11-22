import sys
rom=open(sys.argv[1],'rb').read()
res=[]
for bank in range(len(rom)//0x8000):
    base=bank*0x8000; seg=rom[base:base+0x8000]
    for par in (0,1):
        run=0; start=None
        for i in range(par,0x8000-1,2):
            v=seg[i]|seg[i+1]<<8
            good= v>=0x8000 and (v-0x8000==0 or seg[v-0x8000-1]==0) and seg[v-0x8000]!=0
            if good:
                if run==0: start=i
                run+=1
            else:
                if run>=40: res.append((run,bank,start))
                run=0
        if run>=40: res.append((run,bank,start))
for r in sorted(res,reverse=True)[:20]: print('run %d  ROM %06X  SNES %02X:%04X'%(r[0],r[1]*0x8000+r[2],0x80+r[1],0x8000+r[2]))
