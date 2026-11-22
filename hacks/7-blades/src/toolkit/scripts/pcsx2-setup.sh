#!/bin/sh
# Set up PCSX2 2.4.0 headless (Xvfb) in a cloud session. Running it was approved by the project lead (2026-11-02).
# Usage: sh pcsx2-setup.sh /path/to/BIOS.bin
# Result: /opt/pcsx2/squashfs-root/AppRun, config in /opt/pcsx2/cfg (XDG_CONFIG_HOME), Xvfb on :99.
set -e
BIOS="$1"; [ -f "$BIOS" ] || { echo "usage: $0 BIOS.bin (your own dump)"; exit 1; }
apt-get install -y -q --no-install-recommends libopengl0 libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 \
  xvfb xdotool imagemagick xdelta3 xorriso >/dev/null
mkdir -p /opt/pcsx2 && cd /opt/pcsx2
[ -f pcsx2.AppImage ] || curl -sSL -o pcsx2.AppImage \
  https://github.com/PCSX2/pcsx2/releases/download/v2.4.0/pcsx2-v2.4.0-linux-appimage-x64-Qt.AppImage
[ -d squashfs-root ] || { chmod +x pcsx2.AppImage; ./pcsx2.AppImage --appimage-extract >/dev/null; }
export DISPLAY=:99 LANG=C.UTF-8 XDG_CONFIG_HOME=/opt/pcsx2/cfg
pgrep -x Xvfb >/dev/null || (Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 &)
sleep 1
mkdir -p cfg/PCSX2/bios && cp "$BIOS" cfg/PCSX2/bios/
[ -f cfg/PCSX2/inis/PCSX2.ini ] || timeout 30 squashfs-root/AppRun -testconfig >/dev/null 2>&1 || true
I=cfg/PCSX2/inis/PCSX2.ini
sed -i "s/^SetupWizardIncomplete = true/SetupWizardIncomplete = false/; s/^ConfirmShutdown = true/ConfirmShutdown = false/; \
s/^BIOS = .*/BIOS = $(basename "$BIOS")/; s/^Renderer = -1/Renderer = 13/; s/^Backend = Cubeb/Backend = Null/" $I
echo "PCSX2 ready. Boot: (cd /opt/pcsx2/squashfs-root && DISPLAY=:99 XDG_CONFIG_HOME=/opt/pcsx2/cfg ./AppRun -batch -fastboot -nofullscreen -- game.iso &)"
echo "Pad keys: arrows, Return=Start, l=Circle, k=Cross, j=Square, i=Triangle. F1 saves state slot 1, F3 loads."
