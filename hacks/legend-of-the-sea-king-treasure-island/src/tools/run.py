"""python3 tools/run.py cue in.st out.st 'prog with s:name shots' sheetname  -> shots/sheetname.png (all s: shots, 4 per row)"""
import os, tempfile
import sys; sys.path.insert(0, 'tools')
from emu import *
from play import B
from PIL import Image
cue, st_in, st_out, prog, sheet = sys.argv[1:6]
e = Emu(cue, 'sys')
if st_in != '-': e.load(st_in)
ims = []
for stp in prog.split(','):
    stp = stp.strip()
    if not stp: continue
    if stp[0] == 'w' and stp[1:].isdigit(): e.run(int(stp[1:])); continue
    if stp == 's': e.run(1); e.shot(os.path.join(tempfile.gettempdir(), 'umi_f.png')); ims.append(Image.open(os.path.join(tempfile.gettempdir(), 'umi_f.png')).copy()); continue
    name, _, h = stp.partition(':'); rep = 1
    if '*' in h: h, rep = h.split('*'); rep = int(rep)
    for _ in range(rep):
        m = 0
        for n in name.split('+'): m |= B[n]
        e.run(int(h or 4), m); e.run(20)
if st_out != '-': e.save(st_out)
if ims:
    w, h = ims[0].size; c = min(4, len(ims)); r = (len(ims) + c - 1) // c
    S = Image.new('RGB', (w * c, h * r))
    for i, im in enumerate(ims): S.paste(im, ((i % c) * w, (i // c) * h))
    S.save('shots/%s.png' % sheet)
