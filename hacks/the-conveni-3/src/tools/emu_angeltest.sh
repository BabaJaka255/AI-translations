#!/bin/sh
# wait for state load, press Triangle, capture 6 frames into /tmp/c3/aa.png
E="$(dirname "$0")/emu.sh"
sleep 12
sh $E hold i 0.2
rm -f /tmp/c3/a?.png
for k in 1 2 3 4 5 6; do sleep 1; sh $E shot /tmp/c3/a$k.png 2>/dev/null; done
pgrep -x AppRun.wrapped >/dev/null && echo alive || echo dead
cd /tmp/c3 && python3 -c "
from PIL import Image
s=Image.new('RGB',(1280,720))
for k in range(1,7):
  try: im=Image.open(f'a{k}.png')
  except Exception: continue
  i=k-1; s.paste(im.resize((426,320)),((i%3)*427,(i//3)*360))
s.save('aa.png')"
