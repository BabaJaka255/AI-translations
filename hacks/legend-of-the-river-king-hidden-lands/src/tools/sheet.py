import sys
from PIL import Image
def sheet(paths, out, cols=4, w=320, h=240):
    rows = (len(paths) + cols - 1) // cols
    s = Image.new('RGB', (cols * w, rows * h))
    for i, p in enumerate(paths):
        im = Image.open(p).convert('RGB').resize((w, h))
        s.paste(im, ((i % cols) * w, (i // cols) * h))
    s.save(out)
if __name__ == '__main__':
    sheet(sys.argv[2:], sys.argv[1])
