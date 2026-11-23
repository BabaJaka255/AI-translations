import sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from drive import D, grid
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'iso_en.sfc'),'rb').read()
files=[]
for v in [int(x) for x in sys.argv[1].split(',')]:
    rom=bytearray(src)
    assert rom[0x999F:0x99A3]==bytes.fromhex('afa81200')
    rom[0x999F:0x99A3]=bytes([0xA9,v,0,0xEA])
    open('t/test_lbl.sfc','wb').write(rom)
    import subprocess
    subprocess.run(['python3','t/hold.py','t/test_lbl.sfc','t/p_isl.bin','UP:8 w:4 UP:8 w:4 UP:8 w:4 w:300 UP:16 w:200 shot:t/l%d.png'%v])
    files.append('t/l%d.png'%v)
grid(files,'t/g.png',3)
