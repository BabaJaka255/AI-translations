# Open each game 4 memo book (Items, first row) and save a sheet.
import sys
from drive import *
R = sys.argv[1]; ims = []
for i in range(4):
    g = loadrom(R, 'g4_out1')
    for k in ['A', 'DOWN', 'DOWN', 'A']:
        g.press([k], hold=3, after=40)
    for j in range(i): g.press(['RIGHT'], hold=3, after=20)
    g.press(['A'], hold=3, after=40); g.press(['A'], hold=3, after=90)
    ims.append(g.render())
    if len(sys.argv) > 3: g.shot('%s_%d.png' % (sys.argv[3], i), 3)
sheet(ims, sys.argv[2], cols=4)
