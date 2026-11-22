"""play.py CUE STATE_IN 'actions' STATE_OUT [SHOTPREFIX]
actions: space separated. KEY[xN][:hold] taps (KEY in U D L R X(cross) O(circle) S(square) T(tri) ST SE L1 R1),
 wN wait N frames, hKEY:N hold key N frames, shot (save screenshot), poke:ADDR:HEXBYTES, refresh"""
import sys, re
sys.path.insert(0, 'tools')
from emu import *
import os; SRM=os.environ.get('SRM','save.srm')
from PIL import Image
K = dict(U=UP, D=DOWN, L=LEFT, R=RIGHT, X=CROSS, O=CIRCLE, S=SQUARE, T=TRIANGLE, ST=START, SE=SELECT, L1=L1, R1=R1)
cue, sin, acts, sout = sys.argv[1:5]
pre = sys.argv[5] if len(sys.argv) > 5 else 'shots/p'
e = Emu(cue, 'sys', SRM)
if sin != '-': e.load(sin)
else: e.run(1)
n = 0
for a in acts.split():
    if a.startswith('w'): e.run(int(a[1:])); continue
    if a == 'shot':
        e.shot('%s%02d.png' % (pre, n)); n += 1; continue
    if a == 'refresh': e.refresh(); continue
    if a == 'fixnames':
        import struct
        from table import R
        names={'太郎':'Taro','雄三':'Yuzo','紀子':'Noriko','花子':'Hanako','京子':'Kyoko','一郎':'Ichiro'}
        def enc(s):
            w=[ord(s[k])|ord(s[k+1])<<8 for k in range(0,len(s)-1,2)]
            if len(s)%2: w.append(0x1f00|ord(s[-1]))
            return w
        r=e.ram(); cnt=0
        for jp,en in names.items():
            pat=b''.join(struct.pack('<H',R[c]) for c in jp)+b'\xff\xff'
            rep=b''.join(struct.pack('<H',w) for w in enc(en))+b'\xff\xff'
            i=0
            while True:
                i=r.find(pat,i)
                if i<0: break
                if i < 0x10000 or i > 0x150000: e.write(0x80000000+i, rep); cnt+=1
                i+=len(rep)
        print('fixnames',cnt); continue
    if a.startswith('poke:'):
        _, ad, hx = a.split(':'); e.write(int(ad, 16), bytes.fromhex(hx)); continue
    if a.startswith('h'):
        k, f = a[1:].split(':'); e.run(int(f), K[k]); continue
    m = re.fullmatch(r'([A-Z0-9]+)(?:x(\d+))?(?::(\d+))?', a)
    k, cnt, after = m.group(1), int(m.group(2) or 1), int(m.group(3) or 20)
    for _ in range(cnt): e.tap(K[k], 4, after)
if sout != '-': e.save(sout)
e.shot(pre + 'last.png')
