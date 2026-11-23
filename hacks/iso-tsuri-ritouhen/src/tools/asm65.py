"""Small 65816 assembler built on the opcode table in d65.py.

Syntax (one instruction per line, ';' comments, 'label:' prefixes):
  LDA #$12 / #$1234   immediate; width from .a8/.a16/.i8/.i16 state (REP/SEP update it automatically)
  LDA $12   dp  | LDA $1234 abs | LDA $123456 long   (width from number of hex digits)
  LDA $12,X  LDA $1234,Y  LDA $123456,X  LDA ($12)  LDA ($12),Y  LDA [$12],Y  LDA ($12,X)  LDA $03,S  LDA ($03,S),Y
  BNE label  BRL label  JSR label  JSL label(.l)  JMP label  JML label  MVN $7E,$7F
  label references: name (abs/16-bit, or 24-bit for JSL/JML), name.l forces long, <name low byte not supported
  .db 1,2,$03   .dw $1234,label   .dl label   .org $E10000 (sets pc)   .a8 .a16 .i8 .i16
"""
import re
import d65

MODEMAP = {}
for op, (name, mode) in d65.ops.items():
    MODEMAP.setdefault(name, {})[mode] = op
# accumulator forms
for name, op in (('ASL', 0x0A), ('ROL', 0x2A), ('LSR', 0x4A), ('ROR', 0x6A), ('INC', 0x1A), ('DEC', 0x3A)):
    MODEMAP[name]['a'] = op
    MODEMAP[name].pop('i', None)

IMM_M = {'ORA', 'AND', 'EOR', 'ADC', 'LDA', 'CMP', 'SBC', 'BIT'}
IMM_X = {'LDX', 'LDY', 'CPX', 'CPY'}
IMM_1 = {'REP', 'SEP', 'BRK', 'COP', 'WDM'}

def num(s):
    s = s.strip()
    if s.startswith('$'): return int(s[1:], 16), len(s) - 1
    if s.startswith('%'): return int(s[1:], 2), None
    return int(s, 0), None

class Asm:
    def __init__(self, labels=None):
        self.labels = dict(labels or {})

    def assemble(self, src, org):
        self.org = org
        lines = []
        for raw in src.splitlines():
            l = raw.split(';')[0].strip()
            if l: lines.append(l)
        # two passes
        for pas in (0, 1):
            self.pc = org; out = bytearray(); self.a16 = True; self.i16 = True
            self.chunks = []
            start = org
            for l in lines:
                m = re.match(r'^([A-Za-z_][\w]*):\s*(.*)$', l)
                if m:
                    self.labels[m.group(1)] = self.pc; l = m.group(2)
                    if not l: continue
                b = self.line(l, pas)
                out += b; self.pc += len(b)
        return bytes(out)

    def val(self, s, pas):
        s = s.strip()
        long_ = False
        if s.endswith('.l'): s = s[:-2]; long_ = True
        m = re.match(r'^([A-Za-z_]\w*)\s*([+-]\s*[\$\w]+)?$', s)
        if m and not s.startswith('$'):
            name = m.group(1)
            if name in self.labels: v = self.labels[name]
            elif pas == 0: v = self.pc
            else: raise KeyError(name)
            if m.group(2):
                off = m.group(2).replace(' ', '')
                v += num(off[1:])[0] * (1 if off[0] == '+' else -1)
            return v, (6 if long_ else 4), True
        v, nd = num(s)
        if long_: nd = 6
        return v, nd, False

    def line(self, l, pas):
        parts = l.split(None, 1); mn = parts[0].upper(); arg = parts[1].strip() if len(parts) > 1 else ''
        if mn == '.ORG': self.pc = num(arg)[0]; return b''
        if mn == '.A8': self.a16 = False; return b''
        if mn == '.A16': self.a16 = True; return b''
        if mn == '.I8': self.i16 = False; return b''
        if mn == '.I16': self.i16 = True; return b''
        if mn == '.DB':
            return bytes(self.val(x, pas)[0] & 0xff for x in arg.split(','))
        if mn == '.DW':
            o = bytearray()
            for x in arg.split(','): v = self.val(x, pas)[0]; o += bytes([v & 0xff, (v >> 8) & 0xff])
            return bytes(o)
        if mn == '.DL':
            o = bytearray()
            for x in arg.split(','): v = self.val(x, pas)[0]; o += bytes([v & 0xff, (v >> 8) & 0xff, v >> 16])
            return bytes(o)
        modes = MODEMAP[mn]
        if not arg:
            if 'a' in modes and 'i' not in modes: return bytes([modes['a']])
            return bytes([modes['i']])
        if arg.upper() == 'A': return bytes([modes['a']])
        if mn in IMM_1:
            v = self.val(arg.lstrip('#'), pas)[0]
            if mn == 'REP':
                if v & 0x20: self.a16 = True
                if v & 0x10: self.i16 = True
            if mn == 'SEP':
                if v & 0x20: self.a16 = False
                if v & 0x10: self.i16 = False
            return bytes([modes['1'], v & 0xff])
        if arg.startswith('#'):
            v = self.val(arg[1:], pas)[0]
            wide = self.a16 if mn in IMM_M else self.i16
            op = modes['M'] if mn in IMM_M else modes['X']
            return bytes([op, v & 0xff]) + (bytes([(v >> 8) & 0xff]) if wide else b'')
        if mn in ('MVN', 'MVP'):
            a, b = arg.split(',')
            return bytes([modes['b'], self.val(a, pas)[0], self.val(b, pas)[0]])
        if mn in ('BPL', 'BMI', 'BVC', 'BVS', 'BCC', 'BCS', 'BNE', 'BEQ', 'BRA'):
            t = self.val(arg, pas)[0]; d = t - (self.pc + 2)
            if pas == 1 and not -128 <= d <= 127: raise ValueError('branch out of range: %s' % l)
            return bytes([modes['r'], d & 0xff])
        if mn in ('BRL', 'PER'):
            t = self.val(arg, pas)[0]; d = t - (self.pc + 3)
            return bytes([modes['R'], d & 0xff, (d >> 8) & 0xff])
        if mn in ('JSL', 'JML') and not arg.startswith('['):
            v = self.val(arg, pas)[0]
            return bytes([modes['L'], v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff])
        if mn == 'PEA':
            v = self.val(arg, pas)[0]; return bytes([0xF4, v & 0xff, (v >> 8) & 0xff])
        if mn == 'PEI':
            v = self.val(arg.strip('()'), pas)[0]; return bytes([0xD4, v & 0xff])
        a = arg.replace(' ', '')
        pats = [
            (r'^\((.+),X\)$', {'d': '(d,x)', 'A': '(A,x)'}),
            (r'^\((.+),S\),Y$', {'d': '(s),y'}),
            (r'^\((.+)\),Y$', {'d': '(d),y'}),
            (r'^\[(.+)\],Y$', {'d': '[d],y'}),
            (r'^\[(.+)\]$', {'d': '[d]', 'A': '[A]'}),
            (r'^\((.+)\)$', {'d': '(d)', 'A': '(A)'}),
            (r'^(.+),S$', {'d': 's'}),
            (r'^(.+),X$', {'d': 'dx', 'A': 'Ax', 'L': 'Lx'}),
            (r'^(.+),Y$', {'d': 'dy', 'A': 'Ay'}),
            (r'^(.+)$', {'d': 'd', 'A': 'A', 'L': 'L'}),
        ]
        for pat, mm in pats:
            m = re.match(pat, a, re.I)
            if not m: continue
            v, nd, islabel = self.val(m.group(1), pas)
            if nd is None: nd = 2 if v < 0x100 else (4 if v < 0x10000 else 6)
            size = 'd' if nd <= 2 else ('A' if nd <= 4 else 'L')
            if mn in ('JMP', 'JSR') and size == 'L': size = 'A'
            md = mm.get(size)
            if md is None or md not in modes:
                # promote dp->abs, abs->long
                for alt in ('A', 'L'):
                    if mm.get(alt) in modes: size = alt; md = mm[alt]; break
            if md is None or md not in modes: raise ValueError('bad mode %s %s' % (mn, arg))
            op = modes[md]
            if md in ('d', 'dx', 'dy', '(d)', '(d,x)', '(d),y', '[d]', '[d],y', 's', '(s),y'):
                return bytes([op, v & 0xff])
            if md in ('A', 'Ax', 'Ay', '(A)', '(A,x)', '[A]'):
                return bytes([op, v & 0xff, (v >> 8) & 0xff])
            return bytes([op, v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff])
        raise ValueError('cannot parse: ' + l)

def assemble(src, org, labels=None):
    a = Asm(labels); code = a.assemble(src, org); return code, a.labels
