"""Map fish-name tags: COMM.TIM page 0 holds 72 katakana tags (8px tall, drawn as 64x8 sprites,
4 columns of 18 at u=0/64/128/192, v=48+8k). Redrawn in a 3x5 capitals pixel font."""
import sys
import numpy as np
sys.path.insert(0, 'tools')
import tim

G = {
 'A': '.#.|#.#|###|#.#|#.#', 'B': '##.|#.#|##.|#.#|##.', 'C': '.##|#..|#..|#..|.##', 'D': '##.|#.#|#.#|#.#|##.',
 'E': '###|#..|##.|#..|###', 'F': '###|#..|##.|#..|#..', 'G': '.##|#..|#.#|#.#|.##', 'H': '#.#|#.#|###|#.#|#.#',
 'I': '###|.#.|.#.|.#.|###', 'J': '..#|..#|..#|#.#|.#.', 'K': '#.#|#.#|##.|#.#|#.#', 'L': '#..|#..|#..|#..|###',
 'M': '#...#|##.##|#.#.#|#...#|#...#', 'N': '#..#|##.#|#.##|#..#|#..#', 'O': '.#.|#.#|#.#|#.#|.#.',
 'P': '##.|#.#|##.|#..|#..', 'Q': '.#.|#.#|#.#|#.#|.##', 'R': '##.|#.#|##.|#.#|#.#', 'S': '.##|#..|.#.|..#|##.',
 'T': '###|.#.|.#.|.#.|.#.', 'U': '#.#|#.#|#.#|#.#|###', 'V': '#.#|#.#|#.#|#.#|.#.',
 'W': '#...#|#...#|#.#.#|##.##|#...#', 'X': '#.#|#.#|.#.|#.#|#.#', 'Y': '#.#|#.#|.#.|.#.|.#.', 'Z': '###|..#|.#.|#..|###',
 '-': '..|..|##|..|..', "'": '#|#|.|.|.',
}
SPACE = 3
BG, INK = 14, 1

# sheet order (column by column), English per the script's fish names
NAMES = [
 'Char', 'Sculpin', 'Brook Trout', 'Carp', 'Itomoroko', 'Silver Carp', 'Loach', 'Crucian Carp', 'Aucha Perch',
 'White Crucian', 'Wataka', 'Amur Snakehead', 'Barbel Steed', 'Mullet', 'Bitterling', 'Black Porgy', 'River Prawn', 'Crayfish',
 'Sea-run Char', 'Rainbow Trout', 'Pond Smelt', 'Dark Sleeper', 'Bagrid Catfish', 'Mugitsuku', 'Tamoroko', 'Torrent Catfish',
 'Stickleback', 'Catfish', 'Pike Gudgeon', 'Higai', 'Flathead', 'Sea Bass', 'Eel', 'Starry Flounder', 'Redspot Salmon', 'Turtle',
 'Masu Trout', 'Kokanee', 'Black Bass', 'Pale Chub', 'Masu Salmon', 'Biwa Gudgeon', 'Dark Chub', 'Ricefish', 'Ninespine',
 'Halfbeak', 'False Gudgeon', 'Grass Carp', 'Pacific Redfin', 'Japanese Lates', 'Giant Eel', 'Grass Puffer', 'Newt', 'Softshell Turtle',
 'Redspot Trout', 'Brown Trout', 'Dace', 'Stone Moroko', 'Bighead Carp', 'Rough Sculpin', 'Gold Crucian', 'Bluegill', 'Snakehead',
 'Three-lips', 'Spined Loach', 'Black Carp', 'Goby', 'Sweetfish', 'Minnow', 'Paradise Fish', 'Frog', 'Crab',
]

def render(text):
    cols = []
    for k, c in enumerate(text.upper()):
        if c == ' ':
            cols += [[0] * 5] * SPACE; continue
        rows = G[c].split('|')
        if cols and cols[-1] != [0] * 5: cols.append([0] * 5)
        for x in range(len(rows[0])): cols.append([1 if r[x] == '#' else 0 for r in rows])
    return np.array(cols, int).T          # 5 x w

def patch(comm):
    comm = bytearray(comm)
    t = tim.parse(bytes(comm), 0)
    idx = tim.indices(t).copy()
    for n, name in enumerate(NAMES):
        cx = 64 * (n // 18); y = 48 + 8 * (n % 18)
        g = render(name)
        w = g.shape[1] + 2
        assert w <= 64, (name, w)
        idx[y:y + 8, cx:cx + 64] = 0
        idx[y:y + 8, cx:cx + w] = BG
        idx[y + 1:y + 6, cx + 1:cx + 1 + g.shape[1]][g > 0] = INK
    words = (idx[:, 0::4] | idx[:, 1::4] << 4 | idx[:, 2::4] << 8 | idx[:, 3::4] << 12).astype('<u2')
    o = t['img']['off']
    comm[o:o + words.nbytes] = words.tobytes()
    return bytes(comm)

if __name__ == '__main__':
    from PIL import Image
    out = patch(open('files/TIM/COMM.TIM', 'rb').read())
    tim.to_image(tim.parse(out, 0)).resize((1024, 1024), Image.NEAREST).save('shots/labels.png')
    print(max(render(n).shape[1] + 2 for n in NAMES))
