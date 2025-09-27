"""
CV Renderer - A template-based CV generation system.

A modern utility that maintains a single source of truth for your CV content
and renders it to multiple formats (LaTeX/PDF, HTML) using Jinja2 templates.
"""

__version__ = "1.0.0"
__author__ = "Anton Ugarov"
__email__ = "augarov.swe@gmail.com"

from .renderer import CVRenderer

__all__ = ["CVRenderer"]
