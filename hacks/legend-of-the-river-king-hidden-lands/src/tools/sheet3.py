import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]
W=sum(i.size[0] for i in ims); H=max(i.size[1] for i in ims)
o=Image.new('RGB',(W,H)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.size[0]
o.resize((W*2,H*2),Image.NEAREST).save(sys.argv[1])
