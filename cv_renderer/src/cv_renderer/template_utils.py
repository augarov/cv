"""Utilities exposed to Jinja2 templates."""

from typing import TypeVar
from urllib.parse import urlparse

import phonenumbers
from markdown_it import MarkdownIt
from markupsafe import Markup
from rendercv.renderer.templater.date import format_date_range, format_single_date
from rendercv.schema.models.design.design import Design
from rendercv.schema.models.locale.locale import Locale

# CommonMark with raw HTML escaped; markdown-it's link validation drops
# javascript:, vbscript: and data: (except images) links
_markdown = MarkdownIt("commonmark", {"html": False})

T = TypeVar("T")


def _normalize_path(path: str) -> str:
    normalized_path = "/".join(filter(None, path.split("/")))
    if len(normalized_path) > 0:
        normalized_path = f"/{normalized_path}"
    return normalized_path


def url_path(url: str) -> str:
    """Return only the path component of a URL."""
    parsed_url = urlparse(url)
    return _normalize_path(parsed_url.path)


def markdown_inline(text: str) -> Markup:
    """Render inline markdown to HTML, without a surrounding <p>."""
    return Markup(_markdown.renderInline(text))  # nosec B704 - markdown-it escapes


def markdown_plain(text: str) -> str:
    """Return the text of inline markdown with all formatting removed."""
    parts: list[str] = []
    for block in _markdown.parseInline(text):
        for token in block.children or []:
            if token.type in ("text", "code_inline"):
                parts.append(token.content)
            elif token.type in ("softbreak", "hardbreak"):
                parts.append(" ")
    return "".join(parts)


def single_date(value: str | int, locale: Locale, design: Design) -> str:
    """Format a date the way the PDF does (design.templates.single_date)."""
    result: str = format_single_date(
        value, locale=locale, single_date_template=design.templates.single_date
    )
    return result


def date_range(
    start: str | int, end: str | int | None, locale: Locale, design: Design
) -> str:
    """Format a date range the way the PDF does (design.templates.date_range).

    rendercv's validation already sets ``end_date`` to ``"present"`` when only
    ``start_date`` is given, so ``end`` is ``None`` only for values that didn't
    come from an entry; those show as a single date.
    """
    if end is None:
        return single_date(start, locale, design)
    result: str = format_date_range(
        start,
        end,
        locale=locale,
        single_date_template=design.templates.single_date,
        date_range_template=design.templates.date_range,
    )
    return result


def phone_display(phone: str, design: Design) -> str:
    """Format a ``tel:`` phone the way the PDF header does.

    rendercv stores phones as RFC 3966 ``tel:`` URIs and formats them with
    ``design.header.connections.phone_number_format``. Spaces are non-breaking,
    so the number never wraps.
    """
    number_format = design.header.connections.phone_number_format.upper()
    return phonenumbers.format_number(
        phonenumbers.parse(phone, None),
        getattr(phonenumbers.PhoneNumberFormat, number_format),
    ).replace(" ", "\u00a0")


def as_list(value: T | list[T] | None) -> list[T]:
    """Return value as a list: rendercv allows one value or a list."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]
