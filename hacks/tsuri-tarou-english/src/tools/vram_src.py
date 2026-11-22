"""Find where a savestate's VRAM tiles come from in ROM (raw copies only).
vram_src.py ROM STATE  -> ranges of VRAM (word addr) matched to ROM offsets, 16-byte granularity"""
import sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
import s9xstate as S
rom=open(sys.argv[1],'rb').read(); v=S.get(open(sys.argv[2],'rb').read(),'VRA')
idx={}
for o in range(0,len(rom)-16,2):
    k=rom[o:o+16]
    if len(set(k))>3: idx.setdefault(k,o)
runs=[]
for a in range(0,len(v),16):
    k=v[a:a+16]
    if len(set(k))<=3: continue
    o=idx.get(k)
    if o is None: continue
    if runs and runs[-1][1]==a and runs[-1][3]==o: runs[-1][1]=a+16; runs[-1][3]=o+16
    else: runs.append([a,a+16,o,o+16])
for a,b,o,e in runs:
    if b-a>=64: print('VRAM word %04X-%04X  <- ROM %06X-%06X (%d bytes)'%(a//2,b//2,o,e,b-a))
