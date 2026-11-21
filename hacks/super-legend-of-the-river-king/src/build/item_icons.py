"""Item icons are stored raw (4bpp sprite tiles, 16 tiles per 0x200-byte row) from ROM 0x56000.
The Stereo / Mono record icons (32x16 cells at tile row 12, columns 8-11 and 12-15) carry katakana
ステレオ / モノラル across their lower half. Redraw the record there and write STEREO / MONO."""
B=0x56000
CELLS={'STEREO':(12,8),'MONO':(12,12)}
FONT={
 'S':["###","#..","###","..#","###"], 'T':["###",".#.",".#.",".#.",".#."],
 'E':["###","#..","##.","#..","###"], 'R':["##.","#.#","##.","#.#","#.#"],
 'O':["###","#.#","#.#","#.#","###"], 'M':["#...#","##.##","#.#.#","#...#","#...#"],
 'N':["#..#","##.#","#.##","#..#","#..#"],
}
def rd(rom,o): return [[sum(((rom[o+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)]
def wr(rom,o,t):
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            for k in range(4): p[k]|=((t[y][x]>>k)&1)<<(7-x)
        rom[o+2*y]=p[0]; rom[o+2*y+1]=p[1]; rom[o+16+2*y]=p[2]; rom[o+17+2*y]=p[3]
def apply(rom,orig):
    for text,(tr,tc) in CELLS.items():
        img=[[0]*32 for _ in range(16)]
        for half in range(2):
            for k in range(4):
                t=rd(orig,B+(tr+half)*0x200+(tc+k)*32)
                for y in range(8):
                    for x in range(8): img[half*8+y][k*8+x]=t[y][x]
        bg=img[0][0]; disc=img[3][16]; edge=img[1][12]
        # rebuild the disc's lower half by mirroring the upper half (centre row 8)
        for y in range(10,15):
            src=img[16-y]
            for x in range(32):
                v=src[x]
                if v not in (bg,disc,edge): v=disc        # centre label -> plain disc
                img[y][x]=v
        # text
        glyphs=[FONT[c] for c in text]
        w=sum(len(g[0]) for g in glyphs)+len(glyphs)-1
        x=(32-w)//2
        for g in glyphs:
            for yy in range(5):
                for xx,ch in enumerate(g[yy]):
                    if ch=='#': img[10+yy][x+xx]=0xF
            x+=len(g[0])+1
        for half in range(2):
            for k in range(4):
                wr(rom,B+(tr+half)*0x200+(tc+k)*32,[[img[half*8+y][k*8+xx] for xx in range(8)] for y in range(8)])
