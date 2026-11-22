"""Find text in a ROM before you have a table.

Relative search: games usually store letters/kana in order, so the
*differences* between consecutive characters match the ROM bytes even when
the absolute values are unknown. Search for a word you saw on screen.

For Japanese, kana are matched against gojūon order (with dakuten forms
between, as most fonts lay them out). Try both KANA_ORDERS and check hits by
building a table guess and dumping nearby text.
"""
from __future__ import annotations

# Common font layouts. Each string is one possible ordering of glyphs.
KANA_ORDERS = {
    # あいうえお... in Shift-JIS/JIS order: small kana and voiced forms interleaved
    "hira_jis": "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん",
    "kata_jis": "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴ",
    # plain gojūon, voiced forms elsewhere (common in 8-bit fonts)
    "hira_plain": "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん",
    "kata_plain": "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン",
}


def _order_for(word: str) -> str | None:
    if all("a" <= c <= "z" for c in word) or all("A" <= c <= "Z" for c in word):
        return None  # Latin: plain code-point differences
    for order in KANA_ORDERS.values():
        if all(c in order for c in word):
            return order
    raise ValueError("word mixes scripts or uses characters outside the known orders; "
                     "use only one kana script or only Latin letters")


def relative_search(data: bytes, word: str, order: str | None = None, width: int = 1,
                    endian: str = "little", max_hits: int = 200):
    """Yield (offset, value) where value is the ROM value that encodes word[0]."""
    if len(word) < 3:
        raise ValueError("use at least 3 characters or you'll drown in false hits")
    if order is None:
        order = _order_for(word)
    vals = [order.index(c) if order else ord(c) for c in word]
    diffs = [b - a for a, b in zip(vals, vals[1:])]
    span = width * len(word)
    hits = 0
    for off in range(0, len(data) - span + 1):
        seq = [int.from_bytes(data[off + i * width:off + (i + 1) * width], endian)
               for i in range(len(word))]
        if all(b - a == d for a, b, d in zip(seq, seq[1:], diffs)):
            yield off, seq[0]
            hits += 1
            if hits >= max_hits:
                return


def table_guess(word: str, value: int, order: str | None = None, width: int = 1) -> str:
    """Build a starter .tbl from a relative-search hit, extrapolating the whole alphabet."""
    if order is None:
        order = _order_for(word)
    if not order:
        order = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if word[0].isupper() else "abcdefghijklmnopqrstuvwxyz"
    lines = []
    for i, ch in enumerate(order):
        v = value + i - order.index(word[0])
        if 0 <= v < 1 << (8 * width):
            lines.append(f"{v:0{2 * width}X}={ch}")
    return "\n".join(lines) + "\n"


def find_sjis(data: bytes, min_chars: int = 4):
    """Yield (offset, text) for runs of Shift-JIS Japanese text (DS/PSP/PS1/PS2/PC games)."""
    i, n = 0, len(data)
    while i < n - 1:
        j, chars = i, 0
        while j < n - 1:
            b = data[j]
            if (0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF) and 0x40 <= data[j + 1] <= 0xFC and data[j + 1] != 0x7F:
                j += 2
                chars += 1
            elif 0x20 <= b < 0x7F and chars:
                j += 1
            else:
                break
        if chars >= min_chars:
            try:
                yield i, data[i:j].decode("cp932")
            except UnicodeDecodeError:
                pass
            i = j
        else:
            i += 1
