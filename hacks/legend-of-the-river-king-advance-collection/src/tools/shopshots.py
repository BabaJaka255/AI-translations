# Open each Kawa 3 tackle-shop counter from the g3_shopmenu state and save a sheet.
import sys
from drive import *
R = sys.argv[1] if len(sys.argv) > 1 else 'k34_en.gba'
SHOPS = [('rod', []), ('lure', ['DOWN']), ('hook', ['DOWN', 'DOWN']), ('bait', ['RIGHT']),
         ('fly', ['RIGHT', 'DOWN']), ('items', ['RIGHT', 'DOWN', 'DOWN'])]
ims = []
for name, keys in SHOPS:
    g = loadrom(R, 'g3_shopmenu')
    for k in keys: g.press([k], hold=3, after=10)
    g.press(['A'], hold=3, after=40)
    for k in (['RIGHT'] * int(sys.argv[2]) if len(sys.argv) > 2 else []): g.press([k], hold=3, after=12)
    ims.append(g.render())
sheet(ims, sys.argv[3] if len(sys.argv) > 3 else '../shops.png', cols=3)
