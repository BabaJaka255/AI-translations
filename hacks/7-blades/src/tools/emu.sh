#!/bin/sh
# Drive PCSX2 under Xvfb. Usage: sh emu.sh start [iso] | key <keys...> | hold <key> <sec> | shot <out.png> | stop
# Pad: arrows, Return=Start, k=Cross(O.K. in JP games is Circle=l), l=Circle, j=Square, i=Triangle, BackSpace=Select
# PCSX2 setup lives in /opt/pcsx2 (see notes/emulator.md for how to recreate it in a new session).
export DISPLAY=:99 LANG=C.UTF-8 XDG_CONFIG_HOME=/opt/pcsx2/cfg
win() { xdotool search --name "SLPM|7 BLADES|セブン|PCSX2" | head -1; }
case "$1" in
  start)
    pgrep -x Xvfb >/dev/null || (Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &); sleep 1
    cd /opt/pcsx2/squashfs-root && setsid nohup ./AppRun -batch -fastboot -nofullscreen -- "${2:?give the ISO path}" > /opt/pcsx2/run.log 2>&1 &
    ;;
  key) shift; w=$(win); for k in "$@"; do xdotool windowactivate --sync "$w" 2>/dev/null; xdotool keydown --window "$w" "$k"; sleep 0.12; xdotool keyup --window "$w" "$k"; sleep 0.35; done ;;
  hold) w=$(win); xdotool keydown --window "$w" "$2"; sleep "$3"; xdotool keyup --window "$w" "$2" ;;
  shot) import -window root -crop 1050x624+0+45 +repage -resize 640x480! "$2" 2>/dev/null || import -window root "$2" ;;
  stop) pkill -x AppRun.wrapped ;;
esac
