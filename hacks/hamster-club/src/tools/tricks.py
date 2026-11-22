"""Helpers for the trick animation sheets: which VRAM address each sheet loads
to, and the saved frames to edit from."""
import os, json, glob
from sheet import Sheet

G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# Saved emulator states of the trick animations (only the frames make_art.py uses)
STATES = os.environ.get('HC_STATES', os.path.join(G, 'gfx/states'))

def loads():
    """{file_offset: (dst, vram_bank, order)} for every trick sheet load seen."""
    out = {}
    for f in glob.glob(os.path.join(STATES, 'tr2', 'sheets_*.json')):
        for tid, lst in json.load(open(f)).items():
            for e in lst:
                out[e['file']] = (e['dst'], e['vbk'], e['order'])
    return out

_L = None
def sheets(tid, cache={}):
    """{name: (Sheet, vram, bank, kind)} for the art sheets of trick tid."""
    global _L
    _L = _L or loads()
    out = {}
    for g in json.load(open(os.path.join(G, 'project.json')))['gfx']:
        if g['name'].startswith('trick%02d_' % tid):
            off = int(g['offset'], 16)
            dst, vbk, order = _L[off]
            key = g['name']
            sh = cache.get(key) or Sheet(key)
            cache[key] = sh
            out[key] = (sh, dst, vbk, 'obj' if g.get('order') == 'obj8x16' else 'any')
    return out

def state(tid, n):
    return os.path.join(STATES, 'tr2', 't%d_f%02d.state' % (tid, n))

def nframes(tid):
    return len(glob.glob(os.path.join(STATES, 'tr2', 't%d_f*.state' % tid)))
