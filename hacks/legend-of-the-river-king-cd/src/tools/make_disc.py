"""Build a test disc: real data track 2 plus silent audio tracks. usage: make_disc.py track02.bin outdir"""
import sys,os
src,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
SEC=2352
def silent(name,secs):
    p=os.path.join(out,name)
    if not os.path.exists(p) or os.path.getsize(p)!=secs*SEC:
        with open(p,'wb') as f: f.write(bytes(secs*SEC))
# track 2 starts at LBA 3366 (file sector 0; index 01 at file sector 224 = LBA 3590)
silent('t01.bin',3366)
d2=os.path.join(out,'t02.bin')
if os.path.abspath(src)!=os.path.abspath(d2):
    if os.path.lexists(d2): os.remove(d2)
    os.symlink(os.path.abspath(src),d2)
cue=['FILE "t01.bin" BINARY','  TRACK 01 AUDIO','    INDEX 01 00:00:00',
     'FILE "t02.bin" BINARY','  TRACK 02 MODE1/2352','    INDEX 00 00:00:00','    INDEX 01 00:02:74']
for t in range(3,31):
    silent('t%02d.bin'%t,75*4)
    cue+=['FILE "t%02d.bin" BINARY'%t,'  TRACK %02d AUDIO'%t,'    INDEX 01 00:00:00']
open(os.path.join(out,'game.cue'),'w').write('\n'.join(cue)+'\n')
