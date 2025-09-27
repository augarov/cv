"""HTML AST renderer implementation."""

from .base import ASTRenderer


def escape_html_text(text: str) -> str:
    """Escape special HTML characters and handle newlines in plain text."""
    # Escape special HTML characters
    html_special_chars = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
    }

    for char, replacement in html_special_chars.items():
        text = text.replace(char, replacement)

    # Handle newlines for HTML
    # Handle double newlines as paragraph breaks
    text = text.replace("\n\n", "</p><p>")
    # Handle single newlines as line breaks
    text = text.replace("\n", "<br>")

    # Wrap the entire text in paragraph tags if it contains paragraph breaks
    if "</p><p>" in text:
        text = f"<p>{text}</p>"

    return text


class ASTToHTMLRenderer(ASTRenderer):
    """Renderer for converting AST to HTML."""

    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph for HTML."""
        return f"<p>{children_text}</p>\n"

    def _render_text(self, text: str) -> str:
        """Render plain text for HTML."""
        return escape_html_text(text)

    def _render_strong(self, children_text: str) -> str:
        """Render bold text for HTML."""
        return f"<strong>{children_text}</strong>"

    def _render_linebreak(self) -> str:
        """Render a line break for HTML."""
        return "<br>\n"

    def _render_softbreak(self) -> str:
        """Render a soft break for HTML."""
        return " "
