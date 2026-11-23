"""Automatic checks on translated script files.

Catches the mechanical mistakes that break games or look sloppy, so human
and agent review can focus on the writing itself.
"""
from __future__ import annotations

import re
from collections import Counter

from .table import Table, tokens_in

JP_CHARS = re.compile(r"[぀-ヿ㐀-鿿ｦ-ﾟ]")
_ANY_TOKEN = re.compile(r"<[^<>]*>|\[[0-9A-Fa-f]{2}\]")


def _visible(line: str) -> str:
    return _ANY_TOKEN.sub("", line)


def _width(line: str, token_widths: dict) -> int:
    """Characters a line takes on screen. Tokens count 0 unless the block's
    box gives them a width (e.g. a player name that can be 8 letters)."""
    return len(_visible(line)) + sum(token_widths.get(m.group(0), 0) for m in _ANY_TOKEN.finditer(line))


def check_entry(e: dict, table: Table | None, block: dict) -> list[tuple[str, str]]:
    """Return a list of (severity, message). Severity: error | warn | info."""
    out: list[tuple[str, str]] = []
    jp, en = e.get("jp", ""), e.get("en", "")
    if not en.strip():
        return [("info", "untranslated")]

    box = block.get("box", {})
    breaks = set(box.get("line_tokens", ["<br>"]))
    pages = set(box.get("page_tokens", []))
    ignore = breaks | pages | set(box.get("free_tokens", []))

    src_tokens = sorted(t for t in tokens_in(jp) if t not in ignore)
    dst_tokens = sorted(t for t in tokens_in(en) if t not in ignore)
    if src_tokens != dst_tokens:
        # multiset difference, so a token used fewer times is reported too
        missing = sorted((Counter(src_tokens) - Counter(dst_tokens)).elements())
        extra = sorted((Counter(dst_tokens) - Counter(src_tokens)).elements())
        out.append(("error", f"control codes differ: missing {missing} extra {extra}"))

    if JP_CHARS.search(en):
        out.append(("error", "Japanese characters left in translation"))

    if table is not None:
        err = table.can_encode(en)
        if err:
            out.append(("error", err))
        elif block.get("mode") == "fixed" and len(table.encode(en)) > e.get("length", 0):
            out.append(("error", f"too long for its field ({len(table.encode(en))}/{e['length']} bytes)"))

    # line/box layout
    # an entry may carry its own limit (e.g. one UI string among others)
    max_chars, max_lines = e.get("max_chars", box.get("max_chars")), box.get("max_lines")
    widths = box.get("token_widths", {})
    if max_chars or max_lines:
        text = en.replace("\n", "")
        for t in pages:
            text = text.replace(t, "\x00")
        for page_no, page in enumerate(text.split("\x00"), 1):
            lines = page
            for t in breaks:
                lines = lines.replace(t, "\x01")
            lines = lines.split("\x01")
            if lines and _width(lines[-1], widths) == 0:
                lines = lines[:-1]
            if max_lines and len(lines) > max_lines:
                out.append(("error", f"page {page_no}: {len(lines)} lines, max {max_lines}"))
            for ln in lines:
                w = _width(ln, widths)
                if max_chars and w > max_chars:
                    out.append(("error", f"line too long ({w}/{max_chars}): {_visible(ln)!r}"))

    if "  " in _visible(en) and not box.get("spaces_ok"):
        out.append(("warn", "double space"))
    if re.search(r" (<br>|\n)", en):
        out.append(("warn", "trailing space before line break"))
    if en.count('"') % 2:
        out.append(("warn", "unbalanced double quotes"))
    if re.search(r"\.\.\.\.|…\.", en):
        out.append(("warn", "irregular ellipsis"))
    if "TODO" in en or "???" in en:
        out.append(("warn", "placeholder text"))
    return out


def check_script(script: dict, table: Table | None, block: dict) -> dict:
    report = {"block": script["block"], "total": len(script["entries"]),
              "translated": 0, "errors": 0, "warnings": 0, "issues": []}
    for e in script["entries"]:
        res = check_entry(e, table, block)
        if e.get("en", "").strip():
            report["translated"] += 1
        for sev, msg in res:
            if sev == "info":
                continue
            report["errors" if sev == "error" else "warnings"] += 1
            report["issues"].append({"id": e["id"], "severity": sev, "message": msg})
    return report
