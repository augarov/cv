"""Tests for template_type module."""

from pathlib import Path

import pytest

from cv_renderer.template_type import (
    TemplateType,
    _match_suffixes,
    detect_template_type,
)


class TestDetectTemplateType:
    """Test cases for detect_template_type function."""

    def test_html_template_detection(self):
        """Test detection of HTML templates."""
        # Simple .html file
        template_path = Path("template.html")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

    def test_tex_template_detection(self):
        """Test detection of LaTeX templates."""
        # .tex file
        template_path = Path("template.tex")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

        # .latex file
        template_path = Path("template.latex")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

    def test_jinja2_template_detection(self):
        """Test detection of Jinja2 templates with multiple suffixes."""
        # HTML Jinja2 template
        template_path = Path("cv.html.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

        # LaTeX Jinja2 template
        template_path = Path("cv.tex.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

        # LaTeX Jinja2 template with .latex extension
        template_path = Path("cv.latex.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

    def test_complex_path_detection(self):
        """Test detection with complex file paths."""
        # Nested path with HTML template
        template_path = Path("templates/web/cv.html.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

        # Nested path with LaTeX template
        template_path = Path("templates/latex/cv.tex.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

    def test_unknown_template_type(self):
        """Test handling of unknown template types."""
        # Unknown extension
        template_path = Path("template.txt")
        result = detect_template_type(template_path)
        assert result is None

        # No extension
        template_path = Path("template")
        result = detect_template_type(template_path)
        assert result is None

        # Unsupported template type
        template_path = Path("template.xml")
        result = detect_template_type(template_path)
        assert result is None

    def test_multiple_suffixes_priority(self):
        """Test behavior with multiple relevant suffixes."""
        # File with both HTML and TEX-like suffixes (should match first found)
        # This tests the current implementation behavior
        template_path = Path("template.html.tex")
        result = detect_template_type(template_path)
        # Should return HTML since it's checked first in SUFFIX_TO_TYPE
        assert result == TemplateType.HTML

    def test_case_sensitivity(self):
        """Test case sensitivity of file extensions."""
        # Uppercase extensions should not match (current implementation)
        template_path = Path("template.HTML")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

        template_path = Path("template.TEX")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX

    def test_dot_filename(self):
        """Test handling of edge cases filenames starting with a dot (hidden files)."""
        # File with only extension
        template_path = Path(".html")
        result = detect_template_type(template_path)
        assert result is None

        template_path = Path(".tex")
        result = detect_template_type(template_path)
        assert result is None

        template_path = Path(".latex")
        result = detect_template_type(template_path)
        assert result is None

        template_path = Path(".other")
        result = detect_template_type(template_path)
        assert result is None

        template_path = Path(".tex.html.j2")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

    def test_multiple_dots_in_filename(self):
        """Test files with multiple dots in the name."""
        # Multiple dots before extension
        template_path = Path("my.cv.template.html")
        result = detect_template_type(template_path)
        assert result == TemplateType.HTML

        template_path = Path("resume.v2.final.tex")
        result = detect_template_type(template_path)
        assert result == TemplateType.TEX


class TestMatchSuffixes:
    """Test cases for _match_suffixes helper function."""

    def test_single_suffix_match(self):
        """Test matching single suffixes."""
        filename_suffixes = [".html"]
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is True

        filename_suffixes = [".tex"]
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

    def test_multiple_suffixes_match(self):
        """Test matching with multiple suffixes."""
        filename_suffixes = [".html", ".j2"]
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is True

        filename_suffixes = [".tex", ".j2"]
        suffixes_to_match = [".tex", ".latex"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is True

        filename_suffixes = [".py", ".j2"]
        suffixes_to_match = [".html", ".tex"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

    def test_multiple_targets_match(self):
        """Test matching against multiple target suffixes."""
        filename_suffixes = [".latex"]
        suffixes_to_match = [".tex", ".latex"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is True

        filename_suffixes = [".tex"]
        suffixes_to_match = [".tex", ".latex"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is True

    def test_empty_suffixes(self):
        """Test behavior with empty suffix lists."""
        filename_suffixes = []
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

        filename_suffixes = [".html"]
        suffixes_to_match = []
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

        filename_suffixes = []
        suffixes_to_match = []
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

    def test_partial_matches(self):
        """Test that partial matches don't work."""
        filename_suffixes = [".htm"]
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False

        filename_suffixes = [".htmlx"]
        suffixes_to_match = [".html"]
        assert _match_suffixes(filename_suffixes, suffixes_to_match) is False


class TestTemplateTypeEnum:
    """Test cases for TemplateType enum."""

    def test_enum_values(self):
        """Test that enum values are as expected."""
        assert TemplateType.HTML.value == "html"
        assert TemplateType.TEX.value == "latex"

    def test_enum_members(self):
        """Test that all expected enum members exist."""
        assert hasattr(TemplateType, "HTML")
        assert hasattr(TemplateType, "TEX")
        assert len(list(TemplateType)) == 2


# Integration tests with real file paths (if needed)
class TestRealFilePaths:
    """Integration tests with actual file paths from the project."""

    def test_project_template_files(self):
        """Test detection of actual template files in the project."""
        # Test the actual template files in the project
        html_template = Path("templates/cv.html.j2")
        result = detect_template_type(html_template)
        assert result == TemplateType.HTML

        tex_template = Path("templates/cv.tex.j2")
        result = detect_template_type(tex_template)
        assert result == TemplateType.TEX

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("cv.html", TemplateType.HTML),
            ("cv.tex", TemplateType.TEX),
            ("cv.latex", TemplateType.TEX),
            ("cv.html.j2", TemplateType.HTML),
            ("cv.tex.j2", TemplateType.TEX),
            ("cv.latex.j2", TemplateType.TEX),
            ("cv.txt", None),
            ("cv.py", None),
            ("cv", None),
            ("resume.HTML", TemplateType.HTML),
            ("template.TEX", TemplateType.TEX),
        ],
    )
    def test_parametrized_detection(self, filename, expected):
        """Parametrized test for various filename patterns."""
        template_path = Path(filename)
        result = detect_template_type(template_path)
        assert result == expected
