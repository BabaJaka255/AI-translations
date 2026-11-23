"""Dump every TIM in the given files to view/tim/<name>_<k>.png (all TIMs back to back in a file)."""
import sys, struct, os; sys.path.insert(0, 'tools')
import tim
for fn in sys.argv[1:]:
    d = open(fn, 'rb').read(); off = 0; k = 0
    while off + 8 <= len(d) and struct.unpack_from('<I', d, off)[0] == 0x10:
        try: t = tim.parse(d, off)
        except Exception as ex: print(fn, off, ex); break
        try:
            im = tim.to_image(t)
            if t['bpp'] == 2 or True: pass
            name = 'view/tim/%s_%d.png' % (os.path.basename(fn).split('.')[0], k)
            # 16-bit images are stored per 16bpp pixel; 4/8bpp widened by to_image
            im.save(name)
        except Exception as ex: print(fn, k, 'img', ex)
        print(fn, k, 'bpp', t['bpp'], t['img']['w'], t['img']['h'], 'clut', t['clut'] and (t['clut']['w'], t['clut']['h']))
        off = t['end']; k += 1
