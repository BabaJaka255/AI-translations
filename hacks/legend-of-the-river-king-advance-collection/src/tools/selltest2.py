# Real g3 sell prompt: put one fish in the creel, talk to the fish shop keeper, show the prompt and cursor.
# text=... replaces the prompt (string 27, pointer 0x1AB50) with a test string at 0x3F0000.
import sys, struct
from drive import *
d = bytearray(open(sys.argv[1], 'rb').read())
TEST = [a[5:] for a in sys.argv if a.startswith('text=')]
if TEST:
    import encode_en
    b = encode_en.encode(TEST[0], 'g3')
    d[0x3f0000:0x3f0000 + len(b)] = b
    d[0x1ab50:0x1ab54] = struct.pack('<I', 0x083f0000)
open('../selltest.gba', 'wb').write(d)
g = loadrom('../selltest.gba', 'g3_fish0')
g.wr(0x3000FCD, bytes([1, 12]))
for k, h in [('UP', 16), ('UP', 16)]:
    g.press([k], hold=h, after=20)
for k, h in [('LEFT', 16), ('UP', 8), ('A', 3)]:
    g.press([k], hold=h, after=40)
g.run_frames(60)
g.press(['A'], hold=3, after=120)
ims = [g.render()]
g.press(['RIGHT'], hold=3, after=30); ims.append(g.render())
sheet(ims, sys.argv[2], cols=2)
g.shot('../sell2_big.png', 3)
