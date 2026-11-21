"""Empty gear slots in the tackle window show a placeholder sprite with katakana written down it:
サオ (rod), ウキ (float), オモリ (sinker), ハリ (hook), plus a horizontal 無し ("none").
They live in the raw sprite sheets (4bpp, 16 tiles per 0x200-byte row). Redraw them in English."""
F5={
 'A':[".###.","#...#","#####","#...#","#...#"], 'D':["####.","#...#","#...#","#...#","####."],
 'E':["#####","#....","####.","#....","#####"], 'F':["#####","#....","####.","#....","#...."],
 'H':["#...#","#...#","#####","#...#","#...#"], 'I':["#####","..#..","..#..","..#..","#####"],
 'K':["#...#","#..#.","###..","#..#.","#...#"], 'L':["#....","#....","#....","#....","#####"],
 'N':["#...#","##..#","#.#.#","#..##","#...#"], 'O':[".###.","#...#","#...#","#...#",".###."],
 'R':["####.","#...#","####.","#..#.","#...#"], 'S':[".####","#....",".###.","....#","####."],
 'T':["#####","..#..","..#..","..#..","..#.."],
}
F4={ # 5x4 letters for labels too long to stack at full height with gaps
 'S':[".####","#....","....#","####."], 'I':["#####","..#..","..#..","#####"],
 'N':["#...#","##..#","#.#.#","#..##"], 'K':["#..#.","###..","#..#.","#...#"],
 'E':["#####","####.","#....","#####"], 'R':["####.","#...#","####.","#...#"],
}
# (sheet base, tile row, tile col, width in tiles, height in tiles, text, vertical)
SLOTS=[(0x58000,28,14,2,4,'ROD',True),(0x5C000,4,14,2,4,'FLOAT',True),(0x5C000,4,12,2,4,'SINKER',True),
       (0x5C000,12,14,2,4,'HOOK',True),(0x4C000,26,12,4,2,'NONE',False)]
BG,INK=1,0xF
def rd(rom,o): return [[sum(((rom[o+(k//2)*16+2*y+(k%2)]>>(7-x))&1)<<k for k in range(4)) for x in range(8)] for y in range(8)]
def wr(rom,o,t):
    for y in range(8):
        p=[0,0,0,0]
        for x in range(8):
            for k in range(4): p[k]|=((t[y][x]>>k)&1)<<(7-x)
        rom[o+2*y]=p[0]; rom[o+2*y+1]=p[1]; rom[o+16+2*y]=p[2]; rom[o+17+2*y]=p[3]
def apply(rom,orig):
    for base,tr,tc,w,h,text,vert in SLOTS:
        W,H=w*8,h*8
        # sanity: the cell must be background + white ink only (the katakana placeholder)
        cells=[[0]*W for _ in range(H)]
        for r in range(h):
            for c in range(w):
                t=rd(orig,base+(tr+r)*0x200+(tc+c)*32)
                for y in range(8):
                    for x in range(8): cells[r*8+y][c*8+x]=t[y][x]
        assert {v for row in cells for v in row}<={BG,INK},(text,{v for row in cells for v in row})
        img=[[BG]*W for _ in range(H)]
        if vert:
            font=F5 if 6*len(text)-1<=H-2 else F4
            gh=len(font[text[0]]); step=gh+1; total=step*len(text)-1; y=(H-total)//2; x0=(W-5)//2
            for ch in text:
                for yy,row in enumerate(font[ch]):
                    for xx,v in enumerate(row):
                        if v=='#': img[y+yy][x0+xx]=INK
                y+=step
        else:
            total=6*len(text)-1; x=(W-total)//2; y0=(H-5)//2
            for ch in text:
                for yy,row in enumerate(F5[ch]):
                    for xx,v in enumerate(row):
                        if v=='#': img[y0+yy][x+xx]=INK
                x+=6
        for r in range(h):
            for c in range(w):
                wr(rom,base+(tr+r)*0x200+(tc+c)*32,[[img[r*8+y][c*8+x] for x in range(8)] for y in range(8)])
