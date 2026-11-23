"""Put the logo together (version 3): the original marlin made whole, traced 'Legend of', 'The Sea King' in the localized lettering,
'to TREASURE ISLAND'.   python3 compose.py -> out_logo.png, out_logo_b.png, layers/*.png, previews"""
import sys, os
import numpy as np
from PIL import Image
from eng import *
import marlin, marlin3, legend, legend2, seaking2, subtitle

RAMP_B = [(0.0, (248, 248, 0)), (0.20, (248, 240, 0)), (0.30, (248, 216, 0)), (0.40, (248, 184, 8)), (0.50, (248, 152, 12)),
          (0.60, (248, 112, 8)), (0.70, (248, 72, 12)), (0.80, (248, 40, 0)), (0.90, (248, 24, 0)), (1.0, (232, 16, 0))]
MARLIN = dict(dx=0, dy=0)          # the original marlin stays exactly where the Japanese logo has it
LEGEND = dict(x=131, y=10, scale=0.345)


def parts(table=RAMP):
    a = Canvas(); marlin.paste_layer(a, marlin3.marlin(**MARLIN))
    b = Canvas(); legend.cyan3d(b, legend2.traced(**LEGEND), depth=2)
    c = Canvas(); seaking2.draw(c, table=table)
    d = Canvas(); subtitle.draw(d)
    # drawn in this order: the marlin leaps in front of the lettering, so all of it shows
    return [('1_legend_of', b), ('2_the_sea_king', c), ('3_marlin', a), ('4_to_treasure_island', d)]


def build(table=RAMP, layers=None):
    cv = Canvas()
    for name, lay in parts(table=table):
        lay.a[:5] = False; lay.a[139:] = False       # the game only draws rows 5..138 of the band
        cv.over(lay)
        if layers:
            os.makedirs(layers, exist_ok=True); lay.image().save(os.path.join(layers, name + '.png'))
    return cv


def on_screen(im, y=27):
    bg = Image.open('title_0.png').convert('RGBA')
    scr = bg.copy(); scr.alpha_composite(im.crop((0, 5, 256, 139)), (0, y)); return scr


if __name__ == '__main__':
    # The tester chose colouring B (River King box colours, yellow on top) on 2026-11-22: it is the logo, A is the alternate
    cv = build(RAMP_B, layers='layers')
    im = cv.image(); im.save('out_logo.png')
    cvb = build(RAMP); imb = cvb.image(); imb.save('out_logo_alt.png')
    show(cv, 'v_all.png', 4); show(cvb, 'v_all_b.png', 4)
    show(cv, 'v_top.png', 7, box=(0, 0, 256, 72)); show(cv, 'v_mid.png', 7, box=(0, 36, 256, 106)); show(cv, 'v_bot.png', 7, box=(20, 98, 250, 144))
    on_screen(im).resize((768, 720), Image.NEAREST).save('v_screen.png')
