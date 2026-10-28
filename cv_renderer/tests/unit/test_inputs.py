"""Tests for inputs module."""

import datetime
import logging
from pathlib import Path
from typing import Any

import pytest
from rendercv.renderer.templater.templater import render_full_template

from cv_renderer.inputs import InputError, load_cv, load_website

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _paths(option: str, path: Path) -> dict[str, Any]:
    """Return keyword arguments for load_cv that set one file option."""
    return {option: path}


class TestLoadCv:
    """Test cases for load_cv function."""

    def test_cv_alone_uses_rendercv_defaults(self):
        """Test that cv.yaml alone loads with the classic theme, English, defaults."""
        model = load_cv(FIXTURES / "cv_minimal.yaml")

        assert model.cv.name == "Jane Doe"
        assert model.design.theme == "classic"
        assert model.locale.language == "english"
        assert model.settings.pdf_title == "NAME - CV"
        assert model.settings.current_date == "today"

    def test_full_cv_loads(self):
        """Test that the fixture covering both real CVs' features is valid."""
        model = load_cv(FIXTURES / "cv_full.yaml")

        assert model.cv.sections is not None
        assert set(model.cv.sections) == {
            "summary",
            "experience",
            "education",
            "publications",
            "competitions",
            "skills",
            "languages",
        }

    def test_input_file_path_is_the_cv_file(self):
        """Test that rendercv resolves themes and the photo next to cv.yaml."""
        cv = FIXTURES / "cv_minimal.yaml"

        model = load_cv(cv)

        assert model._input_file_path == cv

    @pytest.mark.parametrize(
        "option, attribute, expected",
        [
            ("design", "design.theme", "engineeringclassic"),
            ("locale", "locale.language", "german"),
            ("settings", "settings.pdf_title", "Fixture title"),
        ],
    )
    def test_file_overrides_its_section(self, option, attribute, expected):
        """Test that design, locale and settings files each set their section."""
        model = load_cv(
            FIXTURES / "cv_minimal.yaml", **_paths(option, FIXTURES / f"{option}.yaml")
        )

        section, field = attribute.split(".")
        assert getattr(getattr(model, section), field) == expected

    def test_settings_file_current_date(self):
        """Test that current_date from settings.yaml is a date."""
        model = load_cv(
            FIXTURES / "cv_minimal.yaml", settings=FIXTURES / "settings.yaml"
        )

        assert model.settings.current_date == datetime.date(2024, 5, 1)

    def test_inline_sections_used_without_files(self):
        """Test that sections inside cv.yaml apply when no file is given."""
        model = load_cv(FIXTURES / "cv_inline_sections.yaml")

        assert model.design.theme == "sb2nov"
        assert model.locale.language == "french"
        assert model.settings.pdf_title == "Inline title"

    def test_file_replaces_inline_section_with_warning(self, caplog):
        """Test that a file wins over an inline section and a warning is logged."""
        with caplog.at_level(logging.WARNING):
            model = load_cv(
                FIXTURES / "cv_inline_sections.yaml",
                design=FIXTURES / "design.yaml",
                locale=FIXTURES / "locale.yaml",
                settings=FIXTURES / "settings.yaml",
            )

        assert model.design.theme == "engineeringclassic"
        assert model.locale.language == "german"
        assert model.settings.pdf_title == "Fixture title"
        warnings = [r.getMessage() for r in caplog.records]
        assert len(warnings) == 3
        for key in ("design", "locale", "settings"):
            assert any(f"`{key}:`" in w and f"{key}.yaml" in w for w in warnings)

    def test_no_warning_without_inline_sections(self, caplog):
        """Test that files without matching inline sections log nothing."""
        with caplog.at_level(logging.WARNING):
            load_cv(FIXTURES / "cv_minimal.yaml", design=FIXTURES / "design.yaml")

        assert caplog.records == []

    @pytest.mark.parametrize("option", ["cv", "design", "locale", "settings"])
    def test_missing_file_names_it(self, option, tmp_path):
        """Test that a missing file gives an error naming it."""
        missing = tmp_path / f"{option}.yaml"
        paths = {"cv": FIXTURES / "cv_minimal.yaml", **_paths(option, missing)}

        with pytest.raises(InputError, match=str(missing)):
            load_cv(**paths)

    @pytest.mark.parametrize(
        "option, fixture, message",
        [
            ("cv", "cv_invalid.yaml", r"cv_invalid\.yaml:3:\d+: cv\.email: "),
            ("design", "design_invalid.yaml", r"design_invalid\.yaml:\d+:\d+: "),
            ("locale", "locale_invalid.yaml", r"locale_invalid\.yaml:\d+:\d+: "),
            (
                "settings",
                "settings_invalid.yaml",
                r"settings_invalid\.yaml:\d+:\d+: settings\.current_date: ",
            ),
        ],
    )
    def test_invalid_file_names_it_with_position(self, option, fixture, message):
        """Test that a schema error names the file, line and column."""
        paths = {
            "cv": FIXTURES / "cv_minimal.yaml",
            **_paths(option, FIXTURES / fixture),
        }

        with pytest.raises(InputError, match=message):
            load_cv(**paths)

    def test_invalid_yaml_names_the_file(self, tmp_path):
        """Test that a YAML syntax error names the file and position."""
        broken = tmp_path / "cv.yaml"
        broken.write_text("cv: [\n", encoding="utf-8")

        with pytest.raises(InputError, match=rf"{broken}:\d+:\d+: .*not a valid YAML"):
            load_cv(broken)

    def test_empty_cv_names_the_file(self, tmp_path):
        """Test that an empty cv.yaml gives an error naming it."""
        empty = tmp_path / "cv.yaml"
        empty.write_text("", encoding="utf-8")

        with pytest.raises(InputError, match=str(empty)):
            load_cv(empty)

    @pytest.mark.parametrize("value", ["", " 3"])
    @pytest.mark.parametrize("in_file", [True, False])
    def test_settings_not_a_mapping_names_the_file(self, tmp_path, value, in_file):
        """Test that an empty or scalar `settings:` names its file."""
        cv = tmp_path / "cv.yaml"
        cv.write_text("cv:\n  name: A B\n", encoding="utf-8")
        settings = tmp_path / "settings.yaml"
        if in_file:
            settings.write_text(f"settings:{value}\n", encoding="utf-8")
        else:
            cv.write_text(f"cv:\n  name: A B\nsettings:{value}\n", encoding="utf-8")
        named = settings if in_file else cv

        with pytest.raises(
            InputError, match=rf"{named}: `settings:` must be a mapping"
        ):
            load_cv(cv, settings=settings if in_file else None)

    def test_overlay_without_its_section(self):
        """Test that a file without its top-level key gives a clear error."""
        design = FIXTURES / "design_no_section.yaml"

        with pytest.raises(InputError, match=rf"{design}: .*`design:`"):
            load_cv(FIXTURES / "cv_minimal.yaml", design=design)


class TestLoadCvSourceDate:
    """Test cases for the source_date argument of load_cv."""

    SOURCE_DATE = datetime.date(2030, 1, 2)

    def test_replaces_unset_current_date(self):
        """Test that the source date is used when current_date isn't set."""
        model = load_cv(FIXTURES / "cv_minimal.yaml", source_date=self.SOURCE_DATE)

        assert model.settings.current_date == self.SOURCE_DATE
        assert model.settings._resolved_current_date == self.SOURCE_DATE

    def test_replaces_today(self, tmp_path):
        """Test that the source date replaces current_date: today."""
        settings = tmp_path / "settings.yaml"
        settings.write_text("settings:\n  current_date: today\n", encoding="utf-8")

        model = load_cv(
            FIXTURES / "cv_minimal.yaml",
            settings=settings,
            source_date=self.SOURCE_DATE,
        )

        assert model.settings.current_date == self.SOURCE_DATE

    def test_explicit_date_in_settings_file_wins(self):
        """Test that current_date from settings.yaml beats the source date."""
        model = load_cv(
            FIXTURES / "cv_minimal.yaml",
            settings=FIXTURES / "settings.yaml",
            source_date=self.SOURCE_DATE,
        )

        assert model.settings.current_date == datetime.date(2024, 5, 1)

    def test_explicit_inline_date_wins(self, tmp_path):
        """Test that current_date from an inline settings section wins too."""
        cv = tmp_path / "cv.yaml"
        cv.write_text(
            "cv:\n  name: Jane Doe\nsettings:\n  current_date: 2024-05-01\n",
            encoding="utf-8",
        )

        model = load_cv(cv, source_date=self.SOURCE_DATE)

        assert model.settings.current_date == datetime.date(2024, 5, 1)

    def test_other_settings_kept(self):
        """Test that applying the source date leaves the other settings alone."""
        settings_without_date = FIXTURES / "cv_inline_sections.yaml"

        model = load_cv(settings_without_date, source_date=self.SOURCE_DATE)

        assert model.settings.pdf_title == "Inline title"
        assert model.settings.current_date == self.SOURCE_DATE

    def test_time_spans_use_source_date(self, tmp_path):
        """Test that "present" time spans in the PDF count up to the source date."""
        cv = tmp_path / "cv.yaml"
        cv.write_text(
            "cv:\n  name: Jane Doe\n  sections:\n    experience:\n"
            "      - company: ACME\n        position: Engineer\n"
            "        start_date: 2020-01\n        end_date: present\n",
            encoding="utf-8",
        )

        typst = render_full_template(load_cv(cv, source_date=self.SOURCE_DATE), "typst")

        # 2020-01 up to 2030-01-02; counted up to today it would be shorter
        assert "10 years" in typst


class TestLoadWebsite:
    """Test cases for load_website function."""

    @pytest.fixture
    def cv(self):
        """Return the full fixture CV, which has a headline."""
        return load_cv(FIXTURES / "cv_full.yaml").cv

    def test_minimal_fills_defaults(self, cv):
        """Test that a website.yaml with only url gets every default."""
        website = load_website(FIXTURES / "website_minimal.yaml", cv)

        assert str(website.url) == "https://example.org/cv/"
        assert str(website.pdf_url) == "https://example.org/cv/cv.pdf"
        assert website.title == "Jane Doe – Software Engineer"
        assert website.author == "Jane Doe"
        assert website.app_name == "Jane Doe"
        assert website.keywords is None
        assert website.source_url is None
        assert website.locale is None
        assert website.pdf_filename is None

    def test_title_without_headline(self):
        """Test that the default title is just the name without a headline."""
        cv = load_cv(FIXTURES / "cv_minimal.yaml").cv

        website = load_website(FIXTURES / "website_minimal.yaml", cv)

        assert website.title == "Jane Doe"

    def test_description_from_summary(self, cv):
        """Test that the default description is the first summary paragraph."""
        website = load_website(FIXTURES / "website_minimal.yaml", cv)

        assert website.description == (
            "Engineer with **10 years** of experience in R&D."
        )

    @pytest.mark.parametrize(
        ("cv_yaml", "expected"),
        [
            (
                "cv:\n  name: A B\n  headline: '**Lead** Engineer'\n",
                "**Lead** Engineer",
            ),
            ("cv:\n  name: A *B*\n", "A *B*"),
        ],
    )
    def test_description_without_summary(self, tmp_path, cv_yaml, expected):
        """Test that without a summary the headline, else the title, is used."""
        path = tmp_path / "cv.yaml"
        path.write_text(cv_yaml, encoding="utf-8")

        website = load_website(FIXTURES / "website_minimal.yaml", load_cv(path).cv)

        assert website.description == expected

    def test_explicit_description_wins(self, cv, tmp_path):
        """Test that a description in website.yaml replaces the summary."""
        path = tmp_path / "website.yaml"
        path.write_text(
            "url: https://example.org/cv\ndescription: Short.\n", encoding="utf-8"
        )

        assert load_website(path, cv).description == "Short."

    def test_explicit_values_win(self, cv):
        """Test that values in the file override the defaults."""
        website = load_website(FIXTURES / "website_full.yaml", cv)

        assert str(website.pdf_url) == "https://cdn.example.org/jane.pdf"
        assert website.title == "Jane Doe – CV"
        assert website.author == "J. Doe"
        assert website.app_name == "janedoe"
        assert website.keywords == "software, engineer"
        assert str(website.source_url) == "https://github.com/janedoe/cv"
        assert website.locale == "en-GB"
        assert website.pdf_filename == "Jane_Doe_CV.pdf"

    @pytest.mark.parametrize(
        "url", ["https://example.org/cv", "https://example.org/cv/"]
    )
    def test_trailing_slash_normalized(self, cv, tmp_path, url):
        """Test that url with or without a slash gives the same url and pdf_url."""
        path = tmp_path / "website.yaml"
        path.write_text(f"url: {url}\n", encoding="utf-8")

        website = load_website(path, cv)

        assert str(website.url) == "https://example.org/cv/"
        assert str(website.pdf_url) == "https://example.org/cv/cv.pdf"

    def test_frozen(self, cv):
        """Test that templates can't change the website model."""
        website = load_website(FIXTURES / "website_minimal.yaml", cv)

        with pytest.raises(Exception):
            website.title = "changed"  # type: ignore[misc]

    def test_invalid_names_file_and_fields(self, cv):
        """Test that a bad url and an unknown (old) key are both reported."""
        path = FIXTURES / "website_invalid.yaml"

        with pytest.raises(InputError, match=str(path)) as e:
            load_website(path, cv)

        assert "url:" in str(e.value)
        assert "pdf_title:" in str(e.value)
        # No follow-up error for the pdf_url derived from the bad url
        assert "pdf_url:" not in str(e.value)

    def test_missing_names_the_file(self, cv, tmp_path):
        """Test that a missing website.yaml gives an error naming it."""
        missing = tmp_path / "website.yaml"

        with pytest.raises(InputError, match=str(missing)):
            load_website(missing, cv)

    def test_invalid_yaml_names_the_file(self, cv, tmp_path):
        """Test that a YAML syntax error in website.yaml names the file."""
        broken = tmp_path / "website.yaml"
        broken.write_text("url: [\n", encoding="utf-8")

        with pytest.raises(InputError, match=str(broken)):
            load_website(broken, cv)

    def test_empty_file_requires_url(self, cv, tmp_path):
        """Test that an empty website.yaml reports the missing url."""
        empty = tmp_path / "website.yaml"
        empty.write_text("", encoding="utf-8")

        with pytest.raises(InputError, match=str(empty)):
            load_website(empty, cv)
