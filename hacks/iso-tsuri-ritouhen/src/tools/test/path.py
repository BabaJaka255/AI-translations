import sys, time; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D
t=time.time()
d=D(sys.argv[1])
def press(b,n=1):
    for _ in range(n): d.step(b,10); d.step(None,12)
d.step(None,600); press('START'); d.step(None,150); d.save('t/p_menu.bin')
press('A'); d.step(None,60); press('A'); press('UP'); press('LEFT'); press('A')   # name "A"
d.step('A',10500); d.step(None,300); d.save('t/p_sea.bin'); d.shot('t/p_sea.png')
d.step(None,200); d.step('DOWN',100); d.step('RIGHT',360); d.step('UP',120); d.step('LEFT',40); d.step(None,480)
d.save('t/p_isl.bin')
for _ in range(3): d.step('UP',8); d.step(None,4)
d.step(None,300); d.step('UP',16); d.step(None,200); d.step('UP',16); d.step(None,200)
d.step('UP',96); d.step('RIGHT',72); d.step('UP',100); d.step(None,120); d.step('LEFT',30); d.step('DOWN',4)
d.step('A',4); d.step(None,390); d.save('t/p_fish.bin'); d.shot('t/p_fish.png')
print('done', time.time()-t)
