"""Replace a few Japanese counter glyphs in the main font (ROM bank 6) with English forms."""
YEN=['................', '................', '................', '................', '................', '................', '................', '................', '................', '................', '.#..#..##..#.#..', '.#..#.#..#.##.#.', '.#..#.####.#..#.', '..###.#....#..#.', '....#.#..#.#..#.', '..##...##..#..#.']
BLANK=["."*16]*16
def ga(g): return 0x30000+(g&0xFF8)*32+(g&7)*16
def put(rom,g,rows):
    a=ga(g)
    for y in range(16):
        bits=[1 if c=='#' else 0 for c in rows[y]]
        l=sum(b<<(7-i) for i,b in enumerate(bits[:8])); r=sum(b<<(7-i) for i,b in enumerate(bits[8:]))
        base=a+(0x80 if y>=8 else 0)+(y&7)
        rom[base]=l; rom[base+8]=r
def apply(rom):
    put(rom,0x000,YEN)     # 円 -> "yen"
    put(rom,0x119,BLANK)   # 尾 (fish counter) -> blank; the count stands alone under "Got"
