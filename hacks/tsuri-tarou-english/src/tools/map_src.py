"""Find VRAM tilemap rows of a savestate in ROM (raw copies, any stride).
map_src.py ROM STATE"""
import sys, collections
sys.path.insert(0,__import__('os').path.dirname(__file__))
import s9xstate as S
rom=open(sys.argv[1],'rb').read(); v=S.get(open(sys.argv[2],'rb').read(),'VRA')
found=collections.Counter()
for a in range(0,len(v)-16,16):
    k=v[a:a+16]
    if len(set(k))<6: continue
    i=rom.find(k)
    if i>=0: found[(a//2&0xFC00, i&~0x7FF)]+=1
for (va,ro),n in sorted(found.items()):
    if n>=2: print('VRAM map %04X <- ROM block %06X  (%d rows of 8 words)'%(va,ro,n))
