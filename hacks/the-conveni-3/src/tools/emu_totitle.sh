#!/bin/sh
# Boot an ISO and stop at the owner screen: taps Start through the logos, waits for the title, taps once more.
E=$(dirname "$0")/emu.sh
sh $E stop; sleep 1; sh $E start "$1"; sleep 25
istitle() { python3 -c "
from PIL import Image; import sys
im=Image.open('/tmp/c3/_t.png').convert('RGB')
n=sum(1 for x in range(95,320,3) for y in range(428,448,2) if (lambda p: p[1]>170 and p[2]>150 and p[0]<140)(im.getpixel((x,y))))
sys.exit(0 if n>15 else 1)"; }
for i in $(seq 1 90); do
  sh $E shot /tmp/c3/_t.png
  if istitle; then sh $E hold Return 0.2; sleep 7; echo "title after $i"; exit 0; fi
  sh $E hold Return 0.15; sleep 1
done
echo "no title"; exit 1
