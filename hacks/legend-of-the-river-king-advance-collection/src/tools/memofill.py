# Memo pages with pokes: fish records at 0x30007DC (4 bytes per species), other memos 1 byte each from 0x300050D.
import sys
from drive import *
R = sys.argv[1]; ims = []
for i, pokes in [(1, [(0x30009dd, [3, 0, 0, 0])])]:
    g = loadrom(R, 'g4_out1')
    for a, b in pokes: g.wr(a, bytes(b))
    for k in ['A', 'DOWN', 'DOWN', 'A']:
        g.press([k], hold=3, after=40)
    for j in range(i): g.press(['RIGHT'], hold=3, after=20)
    g.press(['A'], hold=3, after=40); g.press(['A'], hold=3, after=90)
    ims.append(g.render()); g.shot("../memofill_big.png", 3)
sheet(ims, sys.argv[2], cols=3)
