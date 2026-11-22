import numpy as np
from PIL import Image
def sheet(data, path, cols=16, scale=3, first=0):
    n=len(data)//32
    im=Image.new('L',(cols*9,((n+cols-1)//cols)*9),40)
    for i in range(n):
        t=data[i*32:i*32+32]
        px=np.zeros((8,8),np.uint8)
        for y in range(8):
            for x in range(8):
                b=t[y*4+x//2]; px[y,x]=((b>>4) if x&1 else (b&15))*17
        im.paste(Image.fromarray(px),((i%cols)*9,(i//cols)*9))
    im.resize((im.width*scale,im.height*scale),Image.NEAREST).save(path)
