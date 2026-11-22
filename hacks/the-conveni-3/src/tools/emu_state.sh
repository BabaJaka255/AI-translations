#!/bin/sh
# runstate.sh iso state.p2s : boot PCSX2 straight into a savestate
export DISPLAY=:99 LANG=C.UTF-8 XDG_CONFIG_HOME=/opt/pcsx2/cfg
pkill -x AppRun.wrapped; sleep 1
cd /opt/pcsx2/squashfs-root && setsid nohup ./AppRun -batch -fastboot -nofullscreen -statefile "$2" -- "$1" > /opt/pcsx2/run.log 2>&1 &
