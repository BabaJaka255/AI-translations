"""Tile walker: python3 tools/walk.py cue in.st out.st 'R3,U2,s,C,w60,s' sheet
R/L/U/D<n>: walk n tiles (stops if blocked); C/X/T/Q/S: tap circle/cross/triangle/square/start; wN; s shot."""
import os, tempfile
import sys, struct; sys.path.insert(0, 'tools')
from emu import *
from PIL import Image
cue, sin, sout, prog, sheet = sys.argv[1:6]
e = Emu(cue, 'sys')
if sin != '-': e.load(sin)
import os
if os.environ.get('REFRESH'):
    e.refresh('build_exe.bin', 'files/SLPS_021.72'); import vramfix; vramfix.upload(e)
D = dict(R=RIGHT, L=LEFT, U=UP, D=DOWN); T = dict(C=CIRCLE, X=CROSS, T=TRIANGLE, Q=SQUARE, S=START)
def pos(): r = e.ram(); return (r[0x174205], r[0x174206]), r[0x102bce]
ims = []
for st in prog.split(','):
    st = st.strip()
    if st == 's': e.run(1); e.shot(os.path.join(tempfile.gettempdir(), 'umi_f.png')); ims.append(Image.open(os.path.join(tempfile.gettempdir(), 'umi_f.png')).copy()); continue
    if st[0] == 'w': e.run(int(st[1:])); continue
    if st[0] in T: e.run(4, T[st[0]]); e.run(20); continue
    n = int(st[1:] or 1)
    for _ in range(n):
        p0 = pos()
        for f in range(40):
            e.run(1, D[st[0]])
            if pos() != p0: break
        e.run(6)
    print(st, pos())
if sout != '-': e.save(sout)
if ims:
    c = min(4, len(ims)); r = (len(ims) + c - 1) // c
    S = Image.new('RGB', (256 * c, 240 * r))
    for i, im in enumerate(ims): S.paste(im, ((i % c) * 256, (i // c) * 240))
    S.save('shots/%s.png' % sheet)
