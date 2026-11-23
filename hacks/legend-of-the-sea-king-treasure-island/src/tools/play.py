"""python3 tools/play.py in.st out.st 'START:4,w60,CROSS:4,w30' [shot.png]
steps: NAME:hold[*rep] presses a button (then 20 idle frames), wN waits N frames, s<name> takes shots/<name>.png"""
import sys; sys.path.insert(0, 'tools')
from emu import *
B = dict(CROSS=CROSS, SQUARE=SQUARE, SELECT=SELECT, START=START, UP=UP, DOWN=DOWN, LEFT=LEFT, RIGHT=RIGHT,
         CIRCLE=CIRCLE, TRIANGLE=TRIANGLE, L1=L1, R1=R1)
def go(e, prog):
    for st in prog.split(','):
        st = st.strip()
        if not st: continue
        if st[0] == 'w' and st[1:].isdigit(): e.run(int(st[1:])); continue
        if st[0] == 's' and st[1:2] == ':': e.run(1); e.shot('shots/%s.png' % st[2:]); continue
        name, _, h = st.partition(':'); rep = 1
        if '*' in h: h, rep = h.split('*'); rep = int(rep)
        for _ in range(rep):
            m = 0
            for n in name.split('+'): m |= B[n]
            e.run(int(h or 4), m); e.run(20)
if __name__ == '__main__':
    cue = 'orig.cue' if len(sys.argv) < 5 else sys.argv[4]
    e = Emu(cue, 'sys')
    if sys.argv[1] != '-': e.load(sys.argv[1])
    go(e, sys.argv[3])
    e.run(1); e.shot('shots/last.png')
    if sys.argv[2] != '-': e.save(sys.argv[2])
