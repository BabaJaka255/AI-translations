import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D, grid
d=D(sys.argv[1], sys.argv[2]); every=int(sys.argv[3]); n=int(sys.argv[4]); pre=sys.argv[5]
files=[]
for i in range(n):
    d.step('A',every); f='%s%02d.png'%(pre,i); d.shot(f); files.append(f)
d.save(pre+'end.bin')
from PIL import Image
ims=[Image.open(f).crop((0,176,256,224)) for f in files]
cols=3; rows=(len(ims)+cols-1)//cols
W=Image.new('RGB',(256*cols,48*rows))
for i,im in enumerate(ims): W.paste(im,((i%cols)*256,(i//cols)*48))
W.save(pre+'strip.png')
