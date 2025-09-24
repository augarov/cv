"""
Plain text AST renderer implementation.
"""

from .base import ASTRenderer


class ASTToPlainRenderer(ASTRenderer):
    """Renderer for converting AST to plain text."""

    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph for plain text."""
        return f"{children_text}\n\n"

    def _render_text(self, text: str) -> str:
        """Render plain text - no escaping needed for plain text."""
        return text

    def _render_strong(self, children_text: str) -> str:
        """Render bold text for plain text - just return the text without
        formatting."""
        return children_text

    def _render_linebreak(self) -> str:
        """Render a line break for plain text."""
        return "\n"

    def _render_softbreak(self) -> str:
        """Render a soft break for plain text."""
        return " "
