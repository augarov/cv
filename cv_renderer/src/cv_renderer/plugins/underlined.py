"""Mistune plugin for underlined text using _text_ / __text__ / ___text___ syntax.

Source: https://codeberg.org/randogoth/underlined (CC0 1.0 Universal)
"""

import re

__all__ = ["underlined"]

UNDERLINED = r"\b_{1,3}(?=[^\s_])"
UNDERLINED_END_RE = {
    "_": re.compile(r"(?:(?<!\\)(?:\\\\)*\\_|[^\s_])_(?!_)\b"),
    "__": re.compile(r"(?:(?<!\\)(?:\\\\)*\\_|[^\s_])__(?!_)\b"),
    "___": re.compile(r"(?:(?<!\\)(?:\\\\)*\\_|[^\s_])___(?!_)\b"),
}


def parse_underlined(self, m, state) -> int:  # type: ignore[no-untyped-def]
    """Parse an underlined inline token."""
    pos = m.end()
    marker = m.group(0)
    mlen = len(marker)
    _end_re = UNDERLINED_END_RE[marker]
    m1 = _end_re.search(state.src, pos)
    if not m1:
        state.append_token({"type": "text", "raw": marker})
        return int(pos)
    end_pos = m1.end()
    text = state.src[pos : end_pos - mlen]  # noqa: E203
    prec_pos = self.precedence_scan(m, state, end_pos)
    if prec_pos:
        return int(prec_pos)
    new_state = state.copy()
    new_state.src = text
    new_state.in_underlined = True
    state.append_token(
        {
            "type": "underlined",
            "children": self.render(new_state),
        }
    )
    return int(end_pos)


def underlined(md) -> None:  # type: ignore[no-untyped-def]
    """Mistune plugin: underlined text delimited by _, __, or ___."""
    md.inline.register("underlined", UNDERLINED, parse_underlined, before="emphasis")
