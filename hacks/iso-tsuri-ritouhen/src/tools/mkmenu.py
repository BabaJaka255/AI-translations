import run
def menu_runner():
    r=open('iso.sfc','rb').read()
    R=run.Runner(r,open('st_title.bin','rb').read()); c=R.c
    for i in range(6):
        c.joy=0x1000 if 2<=i<6 else 0
        R.frame()
    return R
