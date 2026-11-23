import sys, re; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D
import s9x_state
d=D(sys.argv[1], 't/p_menu.bin')
def press(b,n=1):
    for _ in range(n): d.step(b,10); d.step(None,12)
press('A'); d.step(None,60); press('A'); press('UP'); press('LEFT'); press('A')
import numpy as np
f=0
while f<40000:
    d.step(None,60); f+=60
    s=d.em.get_screen()
    # sea map: lots of light blue/green, no dark text band at bottom
    if s[200:224].mean()>100: break
print('frames', f, 'minutes', f/60/60)
