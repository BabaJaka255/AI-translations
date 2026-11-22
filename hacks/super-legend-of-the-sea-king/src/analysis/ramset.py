"""ramset.py in.state out.state addr=val16 ...  (addr = WRAM offset, hex)"""
import sys,re
d=bytearray(open(sys.argv[1],'rb').read())
i=d.index(b'\n')+1
while True:
    m=re.match(rb'([A-Z]{3}):(\d{6}):',d[i:i+11]); n=int(m.group(2))
    if m.group(1)==b'RAM': base=i+11; break
    i+=11+n
for kv in sys.argv[3:]:
    a,v=kv.split('='); a=int(a,16); v=int(v,16); d[base+a]=v&255; d[base+a+1]=v>>8
open(sys.argv[2],'wb').write(d)
