"""
LaTeX AST renderer implementation.
"""

from .base import ASTRenderer


def escape_latex_text(text: str) -> str:
    """Escape special LaTeX characters and handle newlines in plain text."""
    if not isinstance(text, str):
        return text

    # Process backslashes first to avoid double-escaping
    text = text.replace("\\", r"\textbackslash{}")

    # Then process other special characters
    latex_special_chars = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "^": r"\textasciicircum{}",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
    }

    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)

    # Handle newlines for LaTeX
    # Handle double newlines as paragraph breaks
    text = text.replace("\n\n", "\n\n\\par\n")
    # Handle single newlines as line breaks
    text = text.replace("\n", " \\\\\n")

    return text


class ASTToLaTeXRenderer(ASTRenderer):
    """Renderer for converting AST to LaTeX."""

    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph for LaTeX."""
        return f"{children_text}\n\n"

    def _render_text(self, text: str) -> str:
        """Render plain text for LaTeX."""
        return escape_latex_text(text)

    def _render_strong(self, children_text: str) -> str:
        """Render bold text for LaTeX."""
        return f"\\textbf{{{children_text}}}"

    def _render_linebreak(self) -> str:
        """Render a line break for LaTeX."""
        return " \\\\\n"

    def _render_softbreak(self) -> str:
        """Render a soft break for LaTeX."""
        return " "
