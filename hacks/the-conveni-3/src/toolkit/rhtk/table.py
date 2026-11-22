"""Thingy-style table files (.tbl) with a few common extensions.

Supported line forms (hex keys may be 1+ bytes, e.g. 8140=　):
    XX=text          ordinary mapping
    /XX=<end>        end-of-string token (text optional, defaults to <end>)
    *XX=<br>         line break (text optional, defaults to <br>); decoded as "<br>\n"
    $XX=<name>,N     control code with N parameter bytes, rendered <name 0A 1F>
    ; comment        lines starting with ';' are ignored, as are blank lines

Decoding is greedy longest-match on bytes. Bytes with no mapping are shown
as [XX] so they survive a round trip. Encoding is greedy longest-match on
text, and also accepts [XX] raw bytes and <name ..> control tokens.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEX = re.compile(r"^[0-9A-Fa-f]+$")
_TOKEN = re.compile(r"<([^<>\s]+)((?:\s+[0-9A-Fa-f]{2})*)\s*>|\[([0-9A-Fa-f]{2})\]")


@dataclass
class Control:
    name: str
    params: int


@dataclass
class Table:
    decode_map: dict[bytes, str] = field(default_factory=dict)
    encode_map: dict[str, bytes] = field(default_factory=dict)
    controls: dict[bytes, Control] = field(default_factory=dict)
    controls_by_name: dict[str, bytes] = field(default_factory=dict)
    end_tokens: dict[bytes, str] = field(default_factory=dict)
    breaks: dict[bytes, str] = field(default_factory=dict)
    max_key: int = 1

    # -- loading ---------------------------------------------------------
    @classmethod
    def load(cls, path: str, encoding: str = "utf-8-sig") -> "Table":
        with open(path, encoding=encoding) as f:
            return cls.parse(f.read())

    @classmethod
    def parse(cls, text: str) -> "Table":
        t = cls()
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.rstrip("\r\n")
            if not line.strip() or line.lstrip().startswith(";"):
                continue
            kind = ""
            if line[0] in "/*$":
                kind, line = line[0], line[1:]
            key, sep, val = line.partition("=")
            if not _HEX.match(key) or len(key) % 2:
                raise ValueError(f"table line {lineno}: bad hex key {key!r}")
            b = bytes.fromhex(key)
            t.max_key = max(t.max_key, len(b))
            if kind == "/":
                t.end_tokens[b] = val or "<end>"
                t.encode_map.setdefault(t.end_tokens[b], b)
            elif kind == "*":
                tok = val or "<br>"
                t.breaks[b] = tok
                t.encode_map.setdefault(tok, b)
            elif kind == "$":
                name, _, n = val.partition(",")
                name = name.strip("<>")
                t.controls[b] = Control(name, int(n or 0))
                t.controls_by_name[name] = b
            else:
                if not sep:
                    raise ValueError(f"table line {lineno}: missing '='")
                t.decode_map[b] = val
                # first mapping wins for encoding, so put preferred forms first
                t.encode_map.setdefault(val, b)
        t._enc_keys = sorted(t.encode_map, key=len, reverse=True)
        return t

    # -- decoding --------------------------------------------------------
    def decode(self, data: bytes, start: int = 0, stop_at_end: bool = True,
               limit: int | None = None) -> tuple[str, int]:
        """Decode from data[start:]. Returns (text, bytes_consumed).

        Stops after an end token when stop_at_end, or at `limit` bytes.
        """
        out: list[str] = []
        i = start
        end = len(data) if limit is None else min(len(data), start + limit)
        while i < end:
            for n in range(min(self.max_key, end - i), 0, -1):
                chunk = bytes(data[i:i + n])
                if chunk in self.end_tokens:
                    out.append(self.end_tokens[chunk])
                    i += n
                    if stop_at_end:
                        return "".join(out), i - start
                    out.append("\n")
                    break
                if chunk in self.breaks:
                    out.append(self.breaks[chunk] + "\n")
                    i += n
                    break
                if chunk in self.controls:
                    c = self.controls[chunk]
                    params = data[i + n:i + n + c.params]
                    ps = "".join(f" {p:02X}" for p in params)
                    out.append(f"<{c.name}{ps}>")
                    i += n + c.params
                    break
                if chunk in self.decode_map:
                    out.append(self.decode_map[chunk])
                    i += n
                    break
            else:
                out.append(f"[{data[i]:02X}]")
                i += 1
        return "".join(out), i - start

    # -- encoding --------------------------------------------------------
    def encode(self, text: str) -> bytes:
        """Encode text. Newlines are formatting only and are dropped, since
        line breaks are written as explicit <br>-style tokens."""
        text = text.replace("\r", "").replace("\n", "")
        out = bytearray()
        i = 0
        while i < len(text):
            m = _TOKEN.match(text, i)
            if m:
                if m.group(3):
                    out.append(int(m.group(3), 16))
                    i = m.end()
                    continue
                name, params = m.group(1), m.group(2).split()
                if name in self.controls_by_name:
                    code = self.controls_by_name[name]
                    expected = self.controls[code].params
                    if len(params) != expected:
                        raise ValueError(f"<{name}> takes {expected} params, got {len(params)}")
                    out += code + bytes(int(p, 16) for p in params)
                    i = m.end()
                    continue
                # otherwise fall through: may be a plain mapping like <end>
            for k in self._enc_keys:
                if text.startswith(k, i):
                    out += self.encode_map[k]
                    i += len(k)
                    break
            else:
                ch = text[i]
                raise ValueError(f"cannot encode {ch!r} (U+{ord(ch):04X}) at position {i}: "
                                 f"add it to the table or font")
        return bytes(out)

    def can_encode(self, text: str) -> str | None:
        """Return None if encodable, else an error message."""
        try:
            self.encode(text)
            return None
        except ValueError as e:
            return str(e)


def tokens_in(text: str) -> list[str]:
    """Control tokens (<...>) and raw bytes ([XX]) in order, for QA comparison of
    source vs target. Raw bytes are usually undocumented codes and must survive."""
    return [m.group(0).upper() if m.group(3) else m.group(0) for m in _TOKEN.finditer(text)]
