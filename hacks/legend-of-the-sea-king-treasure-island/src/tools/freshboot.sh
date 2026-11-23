#!/bin/sh
# Boot test.bin from power-on to the Jetty with walking control; saves st/fb_jetty.st (names Koich/Sachiko)
cd "$(dirname "$0")/.."
python3 tools/fresh.py - 'w600,START,w200,CIRCLE,w100,CIRCLE,w100,CIRCLE,w100,CIRCLE,w100,w300,START,w100,START,w100,CIRCLE,w100,CIRCLE,w100,CIRCLE,w100,w60,START,w60,CIRCLE,w60,CROSS,w60,DOWN,w30,CIRCLE,w100,CROSS,UP,w20,CIRCLE,w60,CIRCLE,w60,x10*CIRCLE,x10*CIRCLE,x10*CIRCLE,x20*CIRCLE,x20*CIRCLE,x20*CIRCLE,x20*CIRCLE,x20*CIRCLE,x20*CIRCLE,CROSS,w30,CIRCLE,w30,DOWN,w10,CIRCLE,w40,CROSS,w30' st/fb0.st fb0 >/dev/null 2>&1
python3 tools/walk.py test.cue st/fb0.st st/fb_jetty.st 'X,w30,s' fb_jetty >/dev/null 2>&1
