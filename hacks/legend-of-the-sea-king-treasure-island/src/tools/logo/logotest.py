"""python3 logotest.py logo.png out_shot.png : put a 256x144 logo band into TITLE.TIM on the beta 2 disc and screenshot the title."""
import sys, os; sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image
from gfx import Tim
from cdsector import write_file
from emu import Emu
logo, shot = sys.argv[1], sys.argv[2]
base = 'TITLE.TIM'   # an English TITLE.TIM from a build (src/gfx_out/TIM/TITLE.TIM)
T = Tim(base, 1)
e = np.array(Image.open(logo).convert('RGBA'))
page = np.dstack([T.rgb(), np.where(T.raw[T.idx] != 0, 255, 0).astype(np.uint8)])
page[64:208] = e[:144]
x0, y0, x1, y1 = 0, 64, 256, 208
T.put(page[..., :3], (x0, y0, x1, y1))
tr = int(np.nonzero(T.raw == 0)[0][0])
T.idx[y0:y1, x0:x1][page[y0:y1, x0:x1, 3] < 128] = tr
T.save('TITLE_test.TIM')
Image.fromarray(np.dstack([T.rgb(), np.where(T.raw[T.idx] != 0, 255, 0).astype(np.uint8)])[64:208]).save('quant_band.png')
img = bytearray(open('beta2.bin', 'rb').read())
write_file(img, 34810, open('TITLE_test.TIM', 'rb').read())
open('test.bin', 'wb').write(img)
open('test.cue', 'w').write('FILE "test.bin" BINARY\n  TRACK 01 MODE2/2352\n    INDEX 01 00:00:00\n')
em = Emu('test.cue', 'sys')
if os.path.exists("pre.st"): em.run(5); em.load("pre.st")
else: em.run(1900); em.save('pre.st')
em.run(6, 8); em.run(150); em.shot(shot.replace(".png", "_a.png")); em.run(6, 8); em.run(150)
em.shot(shot)
em.run(400); em.shot(shot.replace(".png", "_b.png"))
