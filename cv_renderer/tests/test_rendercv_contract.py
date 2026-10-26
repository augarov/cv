"""Contract tests for the rendercv internals cv_renderer relies on.

rendercv documents its CLI and YAML schema but not a Python API. These tests
fail first, and in one obvious place, when an upgrade changes what we use.
"""

import datetime
import inspect
from pathlib import Path

import pytest
import rendercv_fonts
from rendercv.exception import (
    RenderCVUserError,
    RenderCVUserValidationError,
    RenderCVValidationError,
)
from rendercv.renderer.pdf_png import get_package_path
from rendercv.renderer.templater.date import format_date_range, format_single_date
from rendercv.renderer.templater.templater import render_full_template
from rendercv.schema.rendercv_model_builder import (
    build_rendercv_dictionary,
    build_rendercv_model_from_commented_map,
)

from cv_renderer.inputs import load_cv

FIXTURES = Path(__file__).parent / "fixtures"


def _parameters(function):
    return list(inspect.signature(function).parameters)


@pytest.mark.parametrize(
    "function, parameters",
    [
        (build_rendercv_dictionary, ["main_yaml_file", "kwargs"]),
        (
            build_rendercv_model_from_commented_map,
            ["commented_map", "input_file_path", "overlay_sources"],
        ),
        (render_full_template, ["rendercv_model", "file_type"]),
        (get_package_path, []),
        (
            format_date_range,
            [
                "start_date",
                "end_date",
                "locale",
                "single_date_template",
                "date_range_template",
            ],
        ),
        (format_single_date, ["date", "locale", "single_date_template"]),
    ],
)
def test_function_signatures(function, parameters):
    """Test that each rendercv function we call keeps its parameters."""
    assert _parameters(function) == parameters


def test_overlay_and_override_keywords():
    """Test that build_rendercv_dictionary accepts the keywords we pass."""
    dictionary, overlay_sources = build_rendercv_dictionary(
        "cv:\n  name: A\n",
        design_yaml_file="design:\n  theme: sb2nov\n",
        locale_yaml_file="locale:\n  language: german\n",
        settings_yaml_file="settings:\n  pdf_title: T\n",
        overrides={"settings.current_date": "2024-05-01"},
    )

    assert dictionary["design"]["theme"] == "sb2nov"
    assert set(overlay_sources) == {"design", "locale", "settings"}


def test_settings_section_always_created():
    """Test that inputs.py can set settings.current_date without a settings file."""
    dictionary, _ = build_rendercv_dictionary("cv:\n  name: A\n")

    assert "settings" in dictionary


def test_overlay_replaces_inline_section():
    """Test that a file replaces an inline section instead of merging with it."""
    dictionary, _ = build_rendercv_dictionary(
        "cv:\n  name: A\nsettings:\n  pdf_title: Inline\n  bold_keywords: [x]\n",
        settings_yaml_file="settings:\n  pdf_title: File\n",
    )

    assert dictionary["settings"]["pdf_title"] == "File"
    assert "bold_keywords" not in dictionary["settings"]


def test_iso_string_current_date_becomes_a_date():
    """Test that an ISO string override ends up as a date in settings."""
    dictionary, overlay_sources = build_rendercv_dictionary(
        "cv:\n  name: A\n", overrides={"settings.current_date": "2024-05-01"}
    )

    model = build_rendercv_model_from_commented_map(
        dictionary, overlay_sources=overlay_sources
    )

    assert model.settings.current_date == datetime.date(2024, 5, 1)


def test_exception_types():
    """Test the error shapes inputs.py converts into InputError."""
    assert issubclass(RenderCVUserValidationError, Exception)
    assert issubclass(RenderCVUserError, Exception)
    fields = set(inspect.signature(RenderCVValidationError).parameters)
    assert {"schema_location", "yaml_location", "yaml_source", "message"} <= fields


def test_font_folders_exist():
    """Test that rendercv_fonts still exposes its font folders."""
    folders = list(rendercv_fonts.paths_to_font_folders)

    assert folders
    assert all(Path(folder).is_dir() for folder in folders)


def test_package_path_exists():
    """Test that rendercv still bundles its Typst package."""
    assert Path(get_package_path()).is_dir()


class TestModelAttributes:
    """Model attributes the website templates use beyond plain schema fields."""

    @pytest.fixture
    def cv(self):
        """Return the full fixture CV."""
        return load_cv(FIXTURES / "cv_full.yaml").cv

    def test_phone_is_a_tel_uri(self, cv):
        """Test that rendercv stores the phone as an RFC 3966 tel: URI."""
        assert str(cv.phone) == "tel:+41-44-123-45-67"

    def test_social_network_urls(self, cv):
        """Test that rendercv builds the profile URL for each network."""
        urls = {sn.network: str(sn.url) for sn in cv.social_networks}

        assert urls == {
            "LinkedIn": "https://linkedin.com/in/jane-doe",
            "GitHub": "https://github.com/janedoe",
            "Telegram": "https://t.me/jane_doe",
        }

    def test_publication_doi_url(self, cv):
        """Test that rendercv builds doi_url and drops url when there's a DOI."""
        papers = {p.title: p for p in cv.sections["publications"]}

        doi_paper = papers["A Paper With a DOI"]
        assert doi_paper.doi_url == "https://doi.org/10.1000/xyz123"
        assert doi_paper.url is None
        assert papers["A Paper About Things"].doi_url is None
