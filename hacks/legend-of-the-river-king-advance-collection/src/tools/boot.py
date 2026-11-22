import sys,time,pickle
sys.path.insert(0,'.')
from gba import GBA
g=GBA(open('../rom/k34.gba','rb').read(),trace_swi=True)
t=time.time()
for f in range(int(sys.argv[1])):
    g.run_frames(1)
    if f%60==59: g.shot('shots/f%04d.png'%f)
print('time',time.time()-t, 'pc',hex(g.pc),g.halted,g.stopped_err)
from collections import Counter
print(Counter(n for _,n,_ in g.swi_log))
pickle.dump(g.save_state(),open('states/boot.pkl','wb'))
