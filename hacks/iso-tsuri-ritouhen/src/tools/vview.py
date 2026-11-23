import sys
from PIL import Image
def sheet(v,bpp,start,ntiles,cols=32,out='v.png',scale=2):
    rows=(ntiles+cols-1)//cols; im=Image.new('L',(cols*8,rows*8))
    px=im.load(); tb=8*bpp
    for t in range(ntiles):
        o=start+t*tb
        for y in range(8):
            for x in range(8):
                c=0
                for p in range(bpp):
                    b=v[o+(p//2)*16+y*2+(p&1)]
                    c|=((b>>(7-x))&1)<<p
                px[(t%cols)*8+x,(t//cols)*8+y]=c*255//((1<<bpp)-1)
    im.resize((im.width*scale,im.height*scale)).save(out)
if __name__=='__main__':
    v=open(sys.argv[1],'rb').read(); bpp=int(sys.argv[2]); st=int(sys.argv[3],16); n=int(sys.argv[4])
    sheet(v,bpp,st,n,out=sys.argv[5])
