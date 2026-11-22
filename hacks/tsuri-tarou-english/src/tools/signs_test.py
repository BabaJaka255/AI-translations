import sys,subprocess; sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import s9xstate as S
st=open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))),'states','map_spot1_poked.bin'),'rb').read()
ram=bytearray(S.get(st,'RAM')); print('spot',ram[0x8D6],ram[0xA94])
for n in range(1,16):
    ram[0x8D6]=n; ram[0x8D7]=0
    open('sp%02d.bin'%n,'wb').write(S.put(st,'RAM',bytes(ram)))
    subprocess.run(['python3',__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'emu.py'),'tten.sfc','sig%02d_'%n,'press:A wait:120 shot:a','sp%02d.bin'%n],check=True)
from PIL import Image
ims=[Image.open('sig%02d_a.png'%n) for n in range(1,16)]
w,h=ims[0].size
for part,(a,b) in enumerate(((0,8),(8,15))):
    G=Image.new('RGB',(w*4//2*1,h*2//2*1))
    G=Image.new('RGB',(w*4,h*2))
    for i,im in enumerate(ims[a:b]): G.paste(im,((i%4)*w,(i//4)*h))
    G.save('signs_en_%d.png'%(part+1))
