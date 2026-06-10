"""Tests for the underlined mistune plugin and its AST renderers."""

from typing import Any, Dict, List

import mistune
import pytest

from cv_renderer.ast.html_renderer import ASTToHTMLRenderer
from cv_renderer.ast.latex_renderer import ASTToLaTeXRenderer
from cv_renderer.ast.plain_renderer import ASTToPlainRenderer
from cv_renderer.models import MarkdownText
from cv_renderer.plugins.underlined import underlined as underlined_plugin


def _make_parser() -> mistune.Markdown:
    return mistune.create_markdown(renderer="ast", plugins=[underlined_plugin])


def _find_tokens(ast: List[Dict[str, Any]], token_type: str) -> List[Dict[str, Any]]:
    """Recursively collect all tokens of a given type from an AST."""
    results = []
    for token in ast:
        if token.get("type") == token_type:
            results.append(token)
        for child in token.get("children", []):
            if isinstance(child, dict) and child.get("type") == token_type:
                results.append(child)
    return results


class TestUnderlinedPluginParsing:
    """Tests that the plugin produces correct AST tokens."""

    @pytest.mark.parametrize("marker", ["_", "__", "___"])
    def test_single_word_produces_underlined_token(self, marker: str) -> None:
        """Each marker variant produces exactly one underlined token."""
        parser = _make_parser()
        ast = parser(f"{marker}hello{marker}")
        tokens = _find_tokens(ast, "underlined")
        assert len(tokens) == 1

    @pytest.mark.parametrize("marker", ["_", "__", "___"])
    def test_underlined_children_contain_text(self, marker: str) -> None:
        """The underlined token's children carry the wrapped text."""
        parser = _make_parser()
        ast = parser(f"{marker}hello{marker}")
        tokens = _find_tokens(ast, "underlined")
        children = tokens[0].get("children", [])
        assert any(c.get("raw") == "hello" for c in children)

    def test_plain_text_unaffected(self) -> None:
        """Text without underline markers produces no underlined tokens."""
        parser = _make_parser()
        ast = parser("just plain text")
        assert _find_tokens(ast, "underlined") == []

    def test_unclosed_marker_falls_back_to_text(self) -> None:
        """An opening marker with no closing match is treated as plain text."""
        parser = _make_parser()
        ast = parser("_unclosed text without end marker")
        assert _find_tokens(ast, "underlined") == []

    def test_underline_in_sentence(self) -> None:
        """A single underlined span within a sentence is parsed correctly."""
        parser = _make_parser()
        ast = parser("Click _here_ to continue.")
        tokens = _find_tokens(ast, "underlined")
        assert len(tokens) == 1

    def test_bold_and_underline_coexist(self) -> None:
        """Bold (**) and underline (_) markup can appear in the same paragraph."""
        parser = _make_parser()
        ast = parser("**bold** and _underlined_")
        assert _find_tokens(ast, "underlined") != []

    def test_multiple_underlined_spans(self) -> None:
        """Two separate underlined spans are each parsed as distinct tokens."""
        parser = _make_parser()
        ast = parser("_one_ and _two_")
        tokens = _find_tokens(ast, "underlined")
        assert len(tokens) == 2


class TestUnderlinedHTMLRenderer:
    """Tests for HTML rendering of underlined tokens."""

    def _render(self, children_text: str) -> str:
        return ASTToHTMLRenderer()._render_underline(children_text)

    def test_wraps_in_u_tag(self) -> None:
        """Plain text is wrapped in a <u> element."""
        assert self._render("hello") == "<u>hello</u>"

    def test_empty_content(self) -> None:
        """Empty children still produce a valid <u> element."""
        assert self._render("") == "<u></u>"

    def test_nested_markup_preserved(self) -> None:
        """Already-rendered inner markup is preserved inside the <u> tag."""
        assert self._render("<strong>bold</strong>") == "<u><strong>bold</strong></u>"

    def test_full_render_via_ast(self) -> None:
        """An underlined token in a hand-crafted AST renders end-to-end."""
        renderer = ASTToHTMLRenderer()
        ast: List[Dict[str, Any]] = [
            {
                "type": "paragraph",
                "children": [
                    {
                        "type": "underlined",
                        "children": [{"type": "text", "raw": "word"}],
                    }
                ],
            }
        ]
        result = renderer.render_ast(ast)
        assert "<u>word</u>" in result


class TestUnderlinedLaTeXRenderer:
    """Tests for LaTeX rendering of underlined tokens."""

    def _render(self, children_text: str) -> str:
        return ASTToLaTeXRenderer()._render_underline(children_text)

    def test_wraps_in_underline_command(self) -> None:
        r"""Plain text is wrapped in a LaTeX \underline{} command."""
        assert self._render("hello") == r"\underline{hello}"

    def test_empty_content(self) -> None:
        r"""Empty children still produce a valid \underline{} command."""
        assert self._render("") == r"\underline{}"

    def test_nested_markup_preserved(self) -> None:
        r"""Already-rendered inner markup is preserved inside \underline{}."""
        assert self._render(r"\textbf{bold}") == r"\underline{\textbf{bold}}"

    def test_full_render_via_ast(self) -> None:
        """An underlined token in a hand-crafted AST renders end-to-end."""
        renderer = ASTToLaTeXRenderer()
        ast: List[Dict[str, Any]] = [
            {
                "type": "paragraph",
                "children": [
                    {
                        "type": "underlined",
                        "children": [{"type": "text", "raw": "word"}],
                    }
                ],
            }
        ]
        result = renderer.render_ast(ast)
        assert r"\underline{word}" in result


class TestUnderlinedPlainRenderer:
    """Tests for plain-text rendering of underlined tokens (passthrough)."""

    def _render(self, children_text: str) -> str:
        return ASTToPlainRenderer()._render_underline(children_text)

    def test_returns_children_unchanged(self) -> None:
        """Underlined text is passed through without any decoration."""
        assert self._render("hello") == "hello"

    def test_empty_content(self) -> None:
        """Empty underlined span returns an empty string."""
        assert self._render("") == ""

    def test_full_render_via_ast(self) -> None:
        """Underlined token in a hand-crafted AST renders as bare text."""
        renderer = ASTToPlainRenderer()
        ast: List[Dict[str, Any]] = [
            {
                "type": "paragraph",
                "children": [
                    {
                        "type": "underlined",
                        "children": [{"type": "text", "raw": "word"}],
                    }
                ],
            }
        ]
        result = renderer.render_ast(ast)
        assert "word" in result
        assert "<u>" not in result
        assert "underline" not in result


class TestMarkdownTextIntegration:
    """Integration tests: MarkdownText model accepts and parses underlined syntax."""

    def test_underlined_text_accepted(self) -> None:
        """Accepts a string containing underlined syntax without raising."""
        md = MarkdownText(text="_hello_")
        assert md.text == "_hello_"

    def test_underlined_produces_token_in_ast(self) -> None:
        """Parsed AST contains an underlined token for _text_ input."""
        md = MarkdownText(text="_hello_")
        tokens = _find_tokens(md.ast, "underlined")
        assert len(tokens) == 1

    def test_mixed_markup_accepted(self) -> None:
        """Bold and underlined markup can coexist in a MarkdownText value."""
        md = MarkdownText(text="**bold** and _underlined_")
        assert _find_tokens(md.ast, "underlined") != []

    def test_plain_text_still_works(self) -> None:
        """Plain text without any markup still parses without underlined tokens."""
        md = MarkdownText(text="just plain text")
        assert md.text == "just plain text"
        assert _find_tokens(md.ast, "underlined") == []
