"""
Template utilities.

This module provides utilities exposed to Jinja2 templates.
"""

from datetime import datetime


def format_current_time(format: str) -> str:
    """Format current time based on format string."""
    return datetime.now().strftime(format)
