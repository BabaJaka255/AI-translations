"""Boot a cue and play to the opening dialogue. python3 tools/newgame.py test.cue prefix"""
import sys; sys.path.insert(0, 'tools')
from emu import *
from play import go
cue, pre = sys.argv[1], sys.argv[2]
e = Emu(cue, 'sys')
e.run(1800)
go(e, 'START:4,w120,START:4,w120,w600,START:4,w90')
e.save('st/%s_menu.st' % pre)
go(e, 'CIRCLE:4,w60,CIRCLE:4,w120,CIRCLE:4,w120')
go(e, 'START:4,w30,CIRCLE:4,w90,START:4,w30,CIRCLE:4,w90,START:4,w30,CIRCLE:4,w120')
e.run(1); e.shot('shots/%s_1.png' % pre)
e.save('st/%s_d1.st' % pre)
for k in range(2, 7):
    go(e, 'CIRCLE:4,w120'); e.run(1); e.shot('shots/%s_%d.png' % (pre, k))
