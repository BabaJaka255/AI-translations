"""Boot a disc image to the file-select screen with the tester's memory card."""
import sys
import numpy as np
sys.path.insert(0, 'tools')
from emu import *
def is_title(f):
    # yellow "PUSH START BUTTON" / logo: lots of saturated green in the frame
    return f is not None and f.shape[1] in (320, 256) and f[:, :, 1].mean() > 60
def is_fileselect(f):
    if f is None: return False
    h, w, _ = f.shape
    band = f[int(h * .86):int(h * .95), :]
    cyan = (band[:, :, 1] > 150) & (band[:, :, 2] > 150) & (band[:, :, 0] < 120)
    return cyan.sum() > 40
def to_fileselect(cue, state_out=None):
    import os
    e = Emu(cue, 'sys', os.environ.get('SRM','save.srm'))
    e.run(1500)
    for i in range(40):
        if is_fileselect(e.frame): break
        e.tap(START, 6, 60)
    e.run(200)
    if state_out: e.save(state_out)
    return e
if __name__ == '__main__':
    e = to_fileselect(sys.argv[1], sys.argv[2])
    e.shot(sys.argv[3])
