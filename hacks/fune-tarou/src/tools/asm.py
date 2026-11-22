"""Tiny 65816 assembler for the engine hooks: a list of byte strings, ('label', name) and
('bra', opcode, name) for 8-bit relative branches, ('jsr', name) / ('jmp', name) for JSR / JMP to a local label."""


def assemble(items, base):
    """base = SNES address of the first byte (bank in bits 16-23)."""
    labels = {}
    for pass_ in range(2):
        out = bytearray()
        for it in items:
            if isinstance(it, (bytes, bytearray)):
                out += it
            elif isinstance(it, str):
                out += bytes.fromhex(it.replace(' ', ''))
            elif it[0] == 'label':
                labels[it[1]] = len(out)
            elif it[0] == 'bra':
                tgt = labels.get(it[2], len(out) + 2) if pass_ else len(out) + 2
                rel = tgt - (len(out) + 2)
                assert -128 <= rel <= 127, it
                out += bytes([it[1], rel & 0xFF])
            elif it[0] in ('jsr', 'jmp'):
                a = (base + labels.get(it[1], 0)) & 0xFFFF
                out += bytes([0x20 if it[0] == 'jsr' else 0x4C, a & 0xFF, a >> 8])
    return bytes(out), labels
