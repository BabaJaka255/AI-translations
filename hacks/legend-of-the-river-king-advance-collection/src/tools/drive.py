import sys,pickle
sys.path.insert(0,'.')
from gba import GBA
from PIL import Image
def load(name):
    g=GBA(open('../rom/k34.gba','rb').read())
    if name: g.load_state(pickle.load(open('states/%s.pkl'%name,'rb')))
    return g
def save(g,name): pickle.dump(g.save_state(),open('states/%s.pkl'%name,'wb'))
def sheet(ims,path,cols=4):
    w,h=ims[0].size
    W=Image.new('RGB',(w*cols,h*((len(ims)+cols-1)//cols)))
    for i,im in enumerate(ims): W.paste(im,((i%cols)*w,(i//cols)*h))
    W.save(path)
def loadrom(path,name):
    g=GBA(open(path,'rb').read())
    if name: g.load_state(pickle.load(open('states/%s.pkl'%name,'rb')))
    return g
