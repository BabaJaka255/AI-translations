# Release screenshots from the patched ROM into OUTDIR (2x scale).
import sys
from drive import *
R, OUT = sys.argv[1], sys.argv[2]
def out(g, name): g.render(); g.shot('%s/%s.png' % (OUT, name), 2)
# game 3 title menu, file select, name entry
g = loadrom(R, 't3'); g.run_frames(30); g.press(['START'], after=60); out(g, 'g3_01_title_menu')
g.press(['A'], after=120); out(g, 'g3_02_file_select')
g = loadrom(R, 'filesel'); g.run_frames(20)
for i in range(5): g.press(['A'], after=60)
out(g, 'g3_03_name_entry')
# game 3 field status panel and windows
g = loadrom(R, 'g3_field'); g.press(['A'], after=40); out(g, 'g3_04_status_panel')
for name, keys in [('g3_05_food', ['RIGHT']), ('g3_06_bait', ['DOWN']), ('g3_07_items', ['DOWN', 'RIGHT']),
                   ('g3_08_gear', ['DOWN', 'DOWN']), ('g3_10_creel', ['DOWN', 'DOWN', 'RIGHT'])]:
    g = loadrom(R, 'g3_field'); g.press(['A'], after=40)
    for k in keys: g.press([k], hold=3, after=10)
    g.press(['A'], after=60); out(g, name)
    if name == 'g3_08_gear':
        g.press(['A'], hold=3, after=30); out(g, 'g3_09_rods')
# game 4 title menu, brother choice, file select, name entry
g = loadrom(R, 't4'); g.run_frames(30); g.press(['START'], hold=3, after=90); out(g, 'g4_01_title_menu')
g.press(['A'], hold=3, after=60); out(g, 'g4_02_brother')
g.press(['A'], after=90); g.press(['A'], after=200); out(g, 'g4_03_file_select')
g = loadrom(R, 'e4_ken'); g.press(['START'], after=20)
for i in range(3): g.press(['A'], after=90)
out(g, 'g4_04_name_entry')
# v0.6 additions: game 4 windows, game 3 Uocchi, Fishing Memo
for name, keys in [('g4_07_food', ['RIGHT']), ('g4_08_items', ['DOWN', 'RIGHT']), ('g4_09_level', ['DOWN', 'DOWN', 'RIGHT'])]:
    g = loadrom(R, 'g4house'); g.run_frames(5); g.press(['A'], hold=3, after=40)
    for k in keys: g.press([k], hold=3, after=15)
    g.press(['A'], hold=3, after=60); out(g, name)
g = loadrom(R, 'g4p2'); g.press(['A'], hold=3, after=60); out(g, 'g4_10_cooler')
g = loadrom(R, 'g3_tank_en'); out(g, 'g3_11_uocchi_tank')
g = loadrom(R, 'g3_uo2'); g.press(['A'], hold=3, after=90); out(g, 'g3_12_uocchi_menu')
g.press(['A'], hold=3, after=120); out(g, 'g3_13_uocchi_fish')
g = loadrom(R, 'g3_uo2'); g.press(['A'], hold=3, after=90); g.press(['DOWN'], hold=3, after=20); g.press(['A'], hold=3, after=120)
out(g, 'g3_14_uocchi_feed')
g = loadrom(R, 'g3_field'); g.press(['A'], after=40)
for k in ['DOWN', 'RIGHT']: g.press([k], hold=3, after=10)
g.press(['A'], after=60); g.press(['RIGHT'], hold=3, after=20); g.press(['A'], hold=3, after=90); out(g, 'g3_15_fishing_memo')
# v0.7 additions: game 3 tackle shop counters, Uocchi help text, game 4 shop windows
for i, (name, keys) in enumerate([('rods', []), ('lures', ['DOWN']), ('hooks', ['DOWN', 'DOWN']), ('bait', ['RIGHT']),
                                  ('flies', ['RIGHT', 'DOWN']), ('items', ['RIGHT', 'DOWN', 'DOWN'])]):
    g = loadrom(R, 'g3_shopmenu')
    for k in keys: g.press([k], hold=3, after=10)
    g.press(['A'], hold=3, after=40); out(g, 'g3_%02d_shop_%s' % (16 + i, name))
g = loadrom(R, 'g3_uo2'); g.press(['A'], hold=3, after=90)
for i in range(3): g.press(['DOWN'], hold=3, after=20)
g.press(['A'], hold=3, after=120); g.press(['DOWN'], hold=3, after=300); out(g, 'g3_22_uocchi_tank_help')
g = loadrom(R, 'g3_uo2'); g.press(['A'], hold=3, after=90)
for i in range(4): g.press(['DOWN'], hold=3, after=20)
g.press(['A'], hold=3, after=120); g.press(['DOWN'], hold=3, after=150); g.press(['DOWN'], hold=3, after=400)
out(g, 'g3_23_uocchi_ornament_help')
import g4force
for i, name in enumerate(['rods', 'lures', 'hooks', 'bait', 'flies', 'items', 'items2', 'prices']):
    g = g4force.shop(R, i); out(g, 'g4_%02d_shop_%s' % (11 + i, name))
