"""Boot a cue and play through the opening to the first jetty menu. python3 tools/tojetty.py test.cue prefix"""
import sys; sys.path.insert(0, 'tools')
from emu import *
from play import go
cue, pre = sys.argv[1], sys.argv[2]
e = Emu(cue, 'sys')
e.run(1800)
go(e, 'START:4,w120,START:4,w120,w600,START:4,w90')
go(e, 'CIRCLE:4,w60,CIRCLE:4,w120,CIRCLE:4,w120')
go(e, 'START:4,w30,CIRCLE:4,w90,START:4,w30,CIRCLE:4,w90,START:4,w30,CIRCLE:4,w120')
for k in range(5 + 16 + 24): go(e, 'CIRCLE:4,w90')
e.run(1); e.shot('shots/%s_jetty.png' % pre)
e.save('st/%s_jetty.st' % pre)
