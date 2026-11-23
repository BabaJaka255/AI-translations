"""Show any script string in the standard message box, in game: python3 tools/strview.py id [sheet] [A=id,A2=id...]
Loads st/talk0.st (standing next to the Jetty boy), overwrites the boy's line (1113) in RAM with string <id> from
build_exe.bin, points the insert slots at other strings (A = slot 0x80102f10, A2 = 0x80102f54, A3 = f58, A4 = f60,
A5 = f64) and taps Circle through the pages, one shot per page. Numbers ({B}) show whatever the slots hold."""
import sys, os, json, struct; sys.path.insert(0, 'tools')
from emu import *
import numpy as np
from PIL import Image
EXE = open('build_exe.bin', 'rb').read(); BASE = 0x80010000 - 0x800
S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
def addr(i):
    for r in S[i]['refs']:
        if r['kind'] == 'code':
            hi = struct.unpack_from('<I', EXE, int(r['at'], 16) - BASE)[0] & 0xffff
            lo = struct.unpack_from('<h', EXE, int(r['at2'], 16) - BASE)[0]
            return (hi << 16) + lo
        if r['kind'] == 'data':
            return struct.unpack_from('<I', EXE, int(r['at'], 16) - BASE)[0]
    raise SystemExit('no ref for %d' % i)
def words(a):
    o = a - BASE; out = []
    while True:
        w = struct.unpack_from('<H', EXE, o)[0]; out.append(w); o += 2
        if w == 0xffff: return out
sid = int(sys.argv[1]); sheet = sys.argv[2] if len(sys.argv) > 2 else 'sv%d' % sid
SLOT = dict(A=0x102f10, A2=0x102f54, A3=0x102f58, A4=0x102f60, A5=0x102f64)
e = Emu('test.cue', 'sys'); e.load(os.environ.get('ST', 'st/talk0.st'))
e.refresh('build_exe.bin', 'files/SLPS_021.72'); import vramfix; vramfix.upload(e)
w = words(addr(sid)); dst = addr(1113) & 0x1fffff
e.write(0x80000000 + dst, struct.pack('<%dH' % len(w), *w))
for kv in sys.argv[3:]:
    k, v = kv.split('='); e.write(0x80000000 + SLOT[k], struct.pack('<I', addr(int(v))))
if os.environ.get('NAME'):                    # player 1 name, e.g. NAME=WWWWWWWW (up to 8 letters, paired)
    nm = os.environ['NAME']; ws = [ord(nm[k]) | (ord(nm[k + 1]) << 8) if k + 1 < len(nm) else 0x1f00 | ord(nm[k])
                                  for k in range(0, len(nm), 2)]
    e.write(0x80174212, struct.pack('<%dH' % (len(ws) + 1), *ws, 0xffff))
if os.environ.get('NUM'):                     # first number slot ({B}/{C:n}) value
    e.write(0x80102ffc, struct.pack('<I', int(os.environ['NUM'])))
ims = []
def shot():
    a = np.array(e.frame)[:, :, :3].copy()
    if ims and (np.abs(ims[-1].astype(int) - a.astype(int)).max(axis=2) > 30).sum() < 12: return
    ims.append(a)
e.run(4, DOWN); e.run(60); shot()
for _ in range(int(os.environ.get('PAGES', 6))):
    e.run(4, CIRCLE); e.run(50); shot()
c = min(4, len(ims)); rr = (len(ims) + c - 1) // c
Sh = Image.new('RGB', (256 * c, 240 * rr))
for i, a in enumerate(ims): Sh.paste(Image.fromarray(a).resize((256, 240)), ((i % c) * 256, (i // c) * 240))
Sh.save('shots/%s.png' % sheet); print(len(ims), 'shots')
