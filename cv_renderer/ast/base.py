"""
Base AST renderer abstract class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class ASTRenderer(ABC):
    """Base class for AST renderers."""

    def render_ast(self, ast: List[Dict[str, Any]]) -> str:
        """Render AST tokens to output format."""
        return ''.join(self._render_token(token) for token in ast)

    def _render_token(self, token: Dict[str, Any]) -> str:
        """Render a single AST token to output format."""
        token_type = token.get('type', '')

        match token_type:
            case 'paragraph':
                children_text = self._render_children(token)
                return self._render_paragraph(children_text)

            case 'text':
                return self._render_text(token.get('raw', ''))

            case 'strong':
                children_text = self._render_children(token)
                return self._render_strong(children_text)

            case 'linebreak':
                return self._render_linebreak()

            case 'softbreak':
                return self._render_softbreak()

            case _:
                # Handle unknown token types by rendering children if they
                # exist
                return self._render_children(token)

    def _render_children(self, token: Dict[str, Any]) -> str:
        """Render children of a token."""
        children = token.get('children', [])
        return ''.join(self._render_token(child) for child in children)

    # Abstract methods that subclasses must implement
    @abstractmethod
    def _render_paragraph(self, children_text: str) -> str:
        """Render a paragraph."""
        pass

    @abstractmethod
    def _render_text(self, text: str) -> str:
        """Render plain text."""
        pass

    @abstractmethod
    def _render_strong(self, children_text: str) -> str:
        """Render bold text."""
        pass

    @abstractmethod
    def _render_linebreak(self) -> str:
        """Render a line break."""
        pass

    @abstractmethod
    def _render_softbreak(self) -> str:
        """Render a soft break."""
        pass
