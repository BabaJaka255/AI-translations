"""Build the English Tsuri Tarou ROM from the original: build.py ORIGINAL.sfc OUT.sfc"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from expand import fix_checksum
from build_font import patch_fonts
from insert_signs import patch_signs
from insert_story import patch_story
from insert_menus import patch_keyboard, patch_labels, patch_title, patch_sign_names, patch_records, patch_backup_msg, patch_hud
r = bytearray(open(sys.argv[1], 'rb').read())
assert len(r) == 0x100000 and r[0x7FD7] == 0x0A, 'expected the original 8 Mbit ROM'
r += b'\xff' * 0x100000; r[0x7FD7] = 0x0B
patch_fonts(r)
patch_sign_names(r)
end = patch_signs(r)
patch_story(r)
patch_keyboard(r)
patch_title(r)
print('labels: %d glyphs, %d free tiles' % patch_labels(r))
patch_records(r)
patch_backup_msg(r)
patch_hud(r)
s = fix_checksum(r)
open(sys.argv[2], 'wb').write(r)
print('built %s: signs end at %06X, checksum %04X' % (sys.argv[2], end, s))
