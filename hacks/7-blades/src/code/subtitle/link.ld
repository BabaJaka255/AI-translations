OUTPUT_ARCH(mips)
ENTRY(my_play)
SECTIONS
{
  . = 0x6d3200;
  /* crt0's bss-clear loop overshoots by one quadword and zeroes 0x6d3200-0x6d320f */
  .pad : { QUAD(0); QUAD(0); }
  .text : { *(.text*) }
  .rodata : { *(.rodata*) }
  .data : { *(.data*) *(.sdata*) *(.sbss*) *(.bss*) *(COMMON) }
  . = ALIGN(16);
  _end = .;
  /DISCARD/ : { *(.MIPS.*) *(.comment) *(.pdr) *(.gnu.attributes) *(.reginfo) *(.note*) }
}
