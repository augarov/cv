"""
Template utilities.

This module provides utilities exposed to Jinja2 templates.
"""

from datetime import datetime
from urllib.parse import urlparse


def _now() -> datetime:
    return datetime.now()


def _normalize_path(path: str) -> str:
    normalized_path = "/".join(filter(None, path.split("/")))
    if len(normalized_path) > 0:
        normalized_path = f"/{normalized_path}"
    return normalized_path


def format_current_time(format: str) -> str:
    """Format current time based on format string."""
    return _now().strftime(format)


def normalize_url(url: str) -> str:
    """Normalize URL."""
    parsed_url = urlparse(url)
    normalized_path = _normalize_path(parsed_url.path)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{normalized_path}"


def url_path(url: str) -> str:
    """Get the path part of a URL."""
    parsed_url = urlparse(url)
    return _normalize_path(parsed_url.path)


def wrap_in_double_quotes(value: str) -> str:
    """Wrap value in double quotes."""
    return f'"{value}"'
