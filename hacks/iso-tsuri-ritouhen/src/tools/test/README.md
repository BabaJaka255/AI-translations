Emulator test scripts used during development (stable-retro snes9x core, `pip install stable-retro`). They import
tools/drive.py and tools/s9x_state.py; save states (.bin) are written to the current folder. Arguments are ROM and
state paths; a few build a test ROM from build/iso_en.sfc.
- path.py: boot -> name entry -> intro (A held) -> sea map -> Oshima -> Tofu spot -> fishing view, saving states.
- catch.py: test ROM where pressing A in the fishing view jumps to the catch result ($80:9BAA) with a faked fish in RAM.
- label.py: test ROMs forcing the spot label index ($80:999F) to check map labels.
- sram_boot.py / sram_bad.py: boot with SRAM copied from a state / corrupted (erased-records message).
- story.py / timing.py: capture the story crawl / measure its length.
- lock.py / fuzz1.py: lockstep checks. Run the Japanese and the English ROM from the same save state with the same
  inputs (one process per ROM) and compare WRAM snapshots; used to show the patch does not change gameplay.
- cast.py / trace.py / ex.py: cast-distance measurements, fight-variable traces and screenshot grids for the
  fishing notes in docs/ENGINE_NOTES.md.
