# Power on, run the start screen intro, go to the game select, both game titles; save a sheet (and 2x shots).
import sys
from gba import GBA
from drive import sheet
R = sys.argv[1]; out = sys.argv[2]; big = sys.argv[3] if len(sys.argv) > 3 else None
g = GBA(open(R, 'rb').read()); ims = []
def shot(name):
    ims.append(g.render())
    if big: g.shot('%s/%s.png' % (big, name), 2)
g.run_frames(380); shot('start_zoom')
g.run_frames(580); shot('start')
g.press(['START'], hold=3, after=120); shot('select_kawa3')
st = g.save_state()
g.press(['DOWN'], hold=3, after=60); shot('select_kawa4')
g.press(['A'], hold=3, after=360); shot('title_kawa4')
g.load_state(st)
g.press(['A'], hold=3, after=360); shot('title_kawa3')
sheet(ims, out, cols=3)
