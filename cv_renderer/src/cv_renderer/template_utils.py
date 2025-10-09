"""
Template utilities.

This module provides utilities exposed to Jinja2 templates.
"""

from datetime import datetime
from urllib.parse import urlparse


def _now() -> datetime:
    return datetime.now()


def format_current_time(format: str) -> str:
    """Format current time based on format string."""
    return _now().strftime(format)


def normalize_url(url: str) -> str:
    """Normalize URL."""
    parsed_url = urlparse(url)

    normalized_path = "/".join(filter(None, parsed_url.path.split("/")))
    if len(normalized_path) > 0:
        normalized_path = f"/{normalized_path}"

    return f"{parsed_url.scheme}://{parsed_url.netloc}{normalized_path}"
