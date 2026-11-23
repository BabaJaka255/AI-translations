import sys; sys.path.insert(0,'tools')
import os, tempfile
from emu import *
from PIL import Image
import os; e=Emu(os.environ.get('CUE','test.cue'),'sys')
if sys.argv[1]!='-': e.load(sys.argv[1])
ims=[]
for st in sys.argv[2].split(','):
    if st=='s': e.run(1); e.shot(os.path.join(tempfile.gettempdir(), 'umi_f.png')); ims.append(Image.open(os.path.join(tempfile.gettempdir(), 'umi_f.png')).copy()); continue
    if st[0]=='w': e.run(int(st[1:])); continue
    if st[0]=='x':
        k,b=st[1:].split('*'); 
        for _ in range(int(k)): e.run(4, globals()[b]); e.run(20)
        continue
    e.run(4, globals()[st]); e.run(30)
e.save(sys.argv[3])
c=min(6,len(ims)); S=Image.new('RGB',(256*c,240*((len(ims)+c-1)//c)))
for i,im in enumerate(ims): S.paste(im.resize((256,240)),((i%c)*256,(i//c)*240))
S.save('shots/%s.png'%sys.argv[4])
