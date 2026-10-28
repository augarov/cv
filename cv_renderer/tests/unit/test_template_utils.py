"""Tests for template_utils module."""

from pathlib import Path

import pytest
from markupsafe import Markup

from cv_renderer.inputs import load_cv
from cv_renderer.template_utils import (
    as_list,
    date_range,
    markdown_inline,
    markdown_plain,
    phone_display,
    single_date,
    url_path,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"


class TestUrlPath:
    """Test cases for url_path function."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            ("https://augarov.github.io/cv/", "/cv"),
            ("https://augarov.github.io/cv", "/cv"),
            ("https://example.com/a//b/?q=1#frag", "/a/b"),
            ("https://example.com:8080/api", "/api"),
            ("https://example.com/", ""),
            ("https://example.com", ""),
        ],
    )
    def test_path_without_trailing_slash(self, url, expected):
        """Test that the path has a leading slash only and nothing else."""
        assert url_path(url) == expected


class TestMarkdownInline:
    """Test cases for markdown_inline function."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("**bold**", "<strong>bold</strong>"),
            ("*italic*", "<em>italic</em>"),
            ("`code`", "<code>code</code>"),
            ("[link](https://x.com)", '<a href="https://x.com">link</a>'),
            ("plain", "plain"),
        ],
    )
    def test_formatting(self, text, expected):
        """Test bold, italic, code and links, with no surrounding <p>."""
        assert markdown_inline(text) == expected

    def test_escapes_html(self):
        """Test that &, raw HTML and quotes are escaped."""
        assert markdown_inline('R&D <b>x</b> "q"') == (
            "R&amp;D &lt;b&gt;x&lt;/b&gt; &quot;q&quot;"
        )

    def test_returns_markup(self):
        """Test that autoescape won't escape the result a second time."""
        assert isinstance(markdown_inline("x"), Markup)

    @pytest.mark.parametrize(
        "url", ["javascript:alert(1)", "vbscript:x", "data:text/html,x"]
    )
    def test_no_unsafe_links(self, url):
        """Test that markdown-it's link validation drops unsafe schemes."""
        assert "<a" not in markdown_inline(f"[x]({url})")


class TestMarkdownPlain:
    """Test cases for markdown_plain function."""

    def test_removes_formatting(self):
        """Test that formatting goes and text and code stay."""
        text = "**Bold** and *it* with `code` and [a link](https://x.com)"

        assert markdown_plain(text) == "Bold and it with code and a link"

    def test_no_html(self):
        """Test that raw HTML comes out as text, unescaped and without tags."""
        assert markdown_plain("R&D <b>x</b>") == "R&D <b>x</b>"

    def test_line_breaks_become_spaces(self):
        """Test that soft and hard breaks become spaces."""
        assert markdown_plain("a\nb  \nc") == "a b c"


class TestDates:
    """Test cases for single_date and date_range."""

    @pytest.fixture
    def model(self):
        """Return a model with rendercv's default design and locale."""
        return load_cv(FIXTURES / "cv_minimal.yaml")

    @pytest.fixture
    def german(self, tmp_path):
        """Return a model with German month names and custom date templates."""
        design = tmp_path / "design.yaml"
        design.write_text(
            "design:\n  theme: classic\n  templates:\n"
            "    single_date: MONTH_NAME YEAR\n"
            "    date_range: START_DATE bis END_DATE\n"
        )
        return load_cv(
            FIXTURES / "cv_minimal.yaml",
            design=design,
            locale=FIXTURES / "locale.yaml",
        )

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("2024-03", "Mar 2024"),
            ("2024-03-15", "Mar 2024"),
            (2024, "2024"),
            ("present", "present"),
            ("Feb 2024", "Feb 2024"),
        ],
    )
    def test_single_date(self, model, value, expected):
        """Test the date forms rendercv accepts, including free text."""
        assert single_date(value, model.locale, model.design) == expected

    @pytest.mark.parametrize(
        "start, end, expected",
        [
            ("2020-01", "2024-03", "Jan 2020 – Mar 2024"),
            ("2020-01", "present", "Jan 2020 – present"),
            (2020, 2021, "2020 – 2021"),
            ("2020-01", None, "Jan 2020"),
        ],
    )
    def test_date_range(self, model, start, end, expected):
        """Test ranges, present and a missing end date."""
        assert date_range(start, end, model.locale, model.design) == expected

    def test_design_and_locale_are_used(self, german):
        """Test that the design templates and the locale reach rendercv."""
        assert single_date("2024-03", german.locale, german.design) == "März 2024"
        assert (
            date_range("2020-06", "present", german.locale, german.design)
            == "Juni 2020 bis gegenwärtig"
        )

    def test_rendercv_fills_present(self, tmp_path):
        """Test that an entry with only start_date gets end_date "present"."""
        cv = tmp_path / "cv.yaml"
        cv.write_text(
            "cv:\n  name: A\n  sections:\n    experience:\n"
            "      - company: C\n        position: P\n        start_date: 2020-06\n"
        )
        entry = load_cv(cv).cv.sections["experience"][0]

        assert entry.end_date == "present"


class TestPhoneDisplay:
    """Test cases for phone_display."""

    @pytest.mark.parametrize(
        "number_format, expected",
        [
            ("national", "044 123 45 67"),
            ("international", "+41 44 123 45 67"),
            ("E164", "+41441234567"),
        ],
    )
    def test_follows_design(self, tmp_path, number_format, expected):
        """Test that the number shows like in the PDF header, without tel:."""
        design = tmp_path / "design.yaml"
        design.write_text(
            "design:\n  theme: classic\n  header:\n    connections:\n"
            f"      phone_number_format: {number_format}\n"
        )
        model = load_cv(FIXTURES / "cv_full.yaml", design=design)

        assert phone_display(str(model.cv.phone), model.design) == expected


@pytest.mark.parametrize(
    "value, expected", [(None, []), ("a", ["a"]), (["a", "b"], ["a", "b"])]
)
def test_as_list(value, expected):
    """Test that one value, a list and None all become a list."""
    assert as_list(value) == expected
