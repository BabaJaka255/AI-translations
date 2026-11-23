"""Playtest helper: python3 tools/auto.py in.st out.st sheet 'steps'
steps: C/X/T/Q/S/U/D/L/R tap (Cn = n taps), wN wait, s shot, Pn = n x (tap circle + shot), Hdir,n hold dir n frames.
Shots that look the same as the previous one are dropped."""
import sys, os; sys.path.insert(0, 'tools')
from emu import *
import numpy as np
from PIL import Image
sin, sout, sheet, prog = sys.argv[1:5]
e = Emu(os.environ.get('CUE', 'test.cue'), 'sys'); e.load(sin)
import os
if os.environ.get('REFRESH'):
    e.refresh('build_exe.bin', 'files/SLPS_021.72'); import vramfix; vramfix.upload(e)
B = dict(C=CIRCLE, X=CROSS, T=TRIANGLE, Q=SQUARE, S=START, U=UP, D=DOWN, L=LEFT, R=RIGHT)
ims = []
def shot():
    e.run(1); a = np.array(e.frame)[:, :, :3].copy()
    if ims and (np.abs(ims[-1].astype(int) - a.astype(int)).max(axis=2) > 30).sum() < 12: return
    ims.append(a)
for st in prog.split(','):
    st = st.strip()
    if not st: continue
    if st == 's': shot(); continue
    if st[0] == 'w': e.run(int(st[1:])); continue
    if st[0] == 'P':
        for _ in range(int(st[1:])): e.run(4, CIRCLE); e.run(40); shot()
        continue
    if st[0] == 'H':
        d, n = st[1], int(st[2:]); e.run(n, B[d]); continue
    n = int(st[1:] or 1)
    for _ in range(n): e.run(4, B[st[0]]); e.run(26)
e.save(sout)
if ims:
    c = min(6, len(ims)); r = (len(ims) + c - 1) // c
    S = Image.new('RGB', (256 * c, 240 * r))
    for i, a in enumerate(ims): S.paste(Image.fromarray(a).resize((256, 240)), ((i % c) * 256, (i // c) * 240))
    S.save('shots/%s.png' % sheet)
print(len(ims), 'shots')
