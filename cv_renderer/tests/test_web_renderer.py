"""Tests for the website Jinja environment and render_web."""

import json
import re
from datetime import date
from pathlib import Path
from xml.etree import ElementTree

import jinja2
import pytest

from cv_renderer.inputs import InputError, load_cv, load_website
from cv_renderer.web_renderer import make_web_environment, render_web

FIXTURES = Path(__file__).parent / "fixtures"
SOURCE = "{{ value }}"


@pytest.fixture
def model():
    """Return the full fixture CV with a fixed build date."""
    return load_cv(FIXTURES / "cv_full.yaml", source_date=date(2030, 1, 2))


@pytest.fixture
def website(model):
    """Return the full fixture website."""
    return load_website(FIXTURES / "website_full.yaml", model.cv)


def _environment(tmp_path, names):
    for name in names:
        (tmp_path / name).write_text(SOURCE, encoding="utf-8")
    return make_web_environment(tmp_path)


class TestEnvironment:
    """Test cases for make_web_environment."""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("page.html.j2", "&lt;b&gt;"),
            ("sitemap.xml.j2", "&lt;b&gt;"),
            ("params.js.j2", "<b>"),
            ("site.webmanifest.j2", "<b>"),
        ],
    )
    def test_autoescape_by_extension(self, tmp_path, name, expected):
        """Test that only HTML and XML templates are autoescaped."""
        environment = _environment(tmp_path, [name])

        assert environment.get_template(name).render(value="<b>") == expected

    def test_undefined_raises(self, tmp_path):
        """Test that a typo in a template fails instead of rendering empty."""
        environment = _environment(tmp_path, ["page.html.j2"])

        with pytest.raises(jinja2.UndefinedError):
            environment.get_template("page.html.j2").render()

    def test_filters_and_globals(self, tmp_path):
        """Test that the CV filters and globals are registered."""
        environment = make_web_environment(tmp_path)

        assert {
            "markdown",
            "markdown_plain",
            "date_range",
            "single_date",
            "phone_display",
        } <= set(environment.filters)
        assert "url_path" in environment.globals

    def test_markdown_is_not_escaped_twice(self, tmp_path):
        """Test that markdown output survives autoescape unchanged."""
        (tmp_path / "page.html.j2").write_text("{{ value | markdown }}")
        environment = make_web_environment(tmp_path)

        rendered = environment.get_template("page.html.j2").render(value="**R&D**")

        assert rendered == "<strong>R&amp;D</strong>"


class TestRenderWeb:
    """Test cases for render_web."""

    def test_context(self, tmp_path, model, website):
        """Test that the template gets cv, design, locale, website, build_date."""
        template = tmp_path / "page.html.j2"
        template.write_text(
            "{{ cv.name }}|{{ design.theme }}|{{ locale.language }}"
            "|{{ website.author }}|{{ build_date.isoformat() }}",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "nested" / "page.html"

        render_web(model, website, template, output)

        assert output.read_text(encoding="utf-8") == (
            "Jane Doe|classic|english|J. Doe|2030-01-02"
        )

    @pytest.mark.parametrize(
        "source, message",
        [
            ("{{ nope }}", "'nope' is undefined"),
            ("line\n{% if %}", ":2: "),
        ],
    )
    def test_template_errors_name_the_file(
        self, tmp_path, model, website, source, message
    ):
        """Test that template errors become an InputError naming the file."""
        template = tmp_path / "page.html.j2"
        template.write_text(source, encoding="utf-8")

        with pytest.raises(InputError) as error:
            render_web(model, website, template, tmp_path / "page.html")

        assert str(error.value).startswith(str(template))
        assert message in str(error.value)

    def test_missing_template(self, tmp_path, model, website):
        """Test that a missing template names the file."""
        template = tmp_path / "missing.html.j2"

        with pytest.raises(InputError, match="missing.html.j2: template not found"):
            render_web(model, website, template, tmp_path / "page.html")


class TestTemplateErrorLine:
    """Test that a runtime template error names the template line."""

    def test_undefined_attribute_has_line(self, tmp_path, model, website):
        """Test that an undefined attribute error points at its line."""
        template = tmp_path / "page.html.j2"
        template.write_text("ok\nok\n{{ cv.nope }}\n", encoding="utf-8")

        with pytest.raises(InputError, match=r"page\.html\.j2:3: .*nope"):
            render_web(model, website, template, tmp_path / "page.html")


TEMPLATES = Path(__file__).parents[2] / "templates" / "web"


def _render(tmp_path, template, cv="cv_full.yaml", website="website_full.yaml"):
    cv_path = cv if isinstance(cv, Path) else FIXTURES / cv
    website_path = website if isinstance(website, Path) else FIXTURES / website
    model = load_cv(cv_path, source_date=date(2030, 1, 2))
    output = tmp_path / "out" / template.removesuffix(".j2")
    render_web(
        model, load_website(website_path, model.cv), TEMPLATES / template, output
    )
    return output.read_text(encoding="utf-8")


class TestIndexHtml:
    """Test cases for the real index.html.j2."""

    @pytest.fixture
    def html(self, tmp_path):
        """Return index.html rendered from the full fixtures."""
        return _render(tmp_path, "index.html.j2")

    def test_markdown_rendered(self, html):
        """Test that markdown becomes HTML and no ** is left."""
        assert "<strong>10 years</strong>" in html
        assert "<em>fast</em>" in html
        assert "<code>report</code>" in html
        assert (
            '<a href="https://example.org/challenge"><strong>Winner</strong></a>'
            in html
        )
        assert "**" not in html

    def test_escaping(self, html):
        """Test that & in the data is escaped once."""
        assert "R&amp;D" in html
        assert "&amp;amp;" not in html

    def test_script_in_data_is_escaped(self, tmp_path):
        """Test that raw HTML in the data comes out as text."""
        cv = tmp_path / "cv.yaml"
        cv.write_text(
            "cv:\n  name: A B\n  sections:\n    summary:\n"
            '      - "<script>alert(1)</script>"\n',
            encoding="utf-8",
        )

        html = _render(tmp_path, "index.html.j2", cv=cv)

        assert "<script>alert" not in html
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html

    def test_section_order_follows_cv(self, tmp_path):
        """Test that sections come in cv.yaml's order, as in the PDF."""
        cv = tmp_path / "cv.yaml"
        cv.write_text(
            "cv:\n  name: A B\n  sections:\n"
            "    languages:\n      - label: English\n        details: native\n"
            "    projects:\n      - Unknown section text\n"
            "    summary:\n      - Short summary.\n"
            "    skills:\n      - label: Tools\n        details: Git\n",
            encoding="utf-8",
        )

        html = _render(tmp_path, "index.html.j2", cv=cv)

        sections = re.findall(r'class="cvSection (cv\w+)"', html)
        assert sections == [
            "cvContact",
            "cvDownload",
            "cvLanguages",
            "cvSummary",
            "cvSkills",
        ]
        assert "Unknown section text" not in html
        assert "<hr>" not in html.split('class="cvSection cvSkills"')[1]

    def test_dates(self, html):
        """Test that dates follow rendercv's formats, as in the PDF."""
        assert "Mar 2021 – present" in html
        assert "Jan 2018 – Feb 2021" in html
        assert "(2020)" in html
        assert "Feb 2024" in html

    def test_stack_is_a_normal_highlight(self, html):
        """Test that a **Stack:** highlight renders like every other bullet."""
        assert (
            '<li class="achievementItem"><strong>Stack:</strong> '
            "<em>C++20 / Python / Docker</em></li>"
        ) in html
        assert "techStack" not in html

    def test_publication_links(self, html):
        """Test that a publication links its DOI, else its url."""
        assert 'href="https://example.org/paper.pdf"' in html
        assert 'href="https://doi.org/10.1000/xyz123"' in html
        assert "ignored.pdf" not in html

    def test_phone(self, html):
        """Test that the phone link has exactly one tel: and the text none."""
        assert 'href="tel:+41-44-123-45-67"' in html
        assert "tel:tel:" not in html
        assert (
            '<a href="tel:+41-44-123-45-67" class="contactLink">044 123 45 67</a>'
            in (html)
        )

    def test_social_links(self, html):
        """Test that social links use rendercv's URL for each network."""
        for url in (
            "https://linkedin.com/in/jane-doe",
            "https://github.com/janedoe",
            "https://t.me/jane_doe",
        ):
            assert f'href="{url}"' in html

    def test_language(self, html):
        """Test that lang follows website.locale."""
        assert '<html lang="en-GB">' in html
        assert '<meta name="language" content="en-GB">' in html

    def test_meta_description_is_plain(self, html):
        """Test that the description has no markdown or tags."""
        assert (
            '<meta name="description" content="Engineer with 10 years of '
            'experience in R&amp;D.">'
        ) in html

    def test_skill_labels(self, html):
        """Test that every skill label is shown."""
        assert '<h3 class="skillCategoryName">Programming</h3>' in html
        assert '<h3 class="skillCategoryName">Tools</h3>' in html

    def test_no_keywords_without_keywords(self, tmp_path):
        """Test that the keywords tag is left out when not set."""
        html = _render(tmp_path, "index.html.j2", website="website_minimal.yaml")

        assert 'name="keywords"' not in html
        assert '<html lang="en">' in html


class TestOtherTemplates:
    """Test cases for sitemap, webmanifest and template_params."""

    def test_sitemap(self, tmp_path):
        """Test that the sitemap is well-formed and lastmod is the build date."""
        root = ElementTree.fromstring(_render(tmp_path, "sitemap.xml.j2"))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        assert [e.text for e in root.findall("s:url/s:loc", ns)] == [
            "https://example.org/cv/",
            "https://cdn.example.org/jane.pdf",
        ]
        assert {e.text for e in root.findall("s:url/s:lastmod", ns)} == {"2030-01-02"}

    def test_webmanifest_with_quotes(self, tmp_path):
        """Test that a title with quotes still gives valid JSON."""
        website = tmp_path / "website.yaml"
        website.write_text(
            "url: https://example.org/cv\ntitle: 'Jane \"JD\" Doe'\n", encoding="utf-8"
        )

        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2", website=website))

        assert manifest["name"] == 'Jane "JD" Doe'
        assert manifest["short_name"] == "Jane Doe"
        assert manifest["icons"][0]["src"] == (
            "/cv/img/favicon/web-app-manifest-192x192.png"
        )

    def test_template_params_null(self, tmp_path):
        """Test that missing values become null."""
        js = _render(tmp_path, "template_params.js.j2", website="website_minimal.yaml")

        assert "locale: null," in js
        assert "sourceUrl: null," in js

    def test_template_params_escaped(self, tmp_path):
        """Test that quotes and </script> stay inside a valid literal."""
        website = tmp_path / "website.yaml"
        website.write_text(
            "url: https://example.org/cv\nlocale: '\"</script>'\n"
            "source_url: https://github.com/janedoe/cv\n",
            encoding="utf-8",
        )

        js = _render(tmp_path, "template_params.js.j2", website=website)

        assert 'locale: "\\"\\u003c/script\\u003e",' in js
        assert 'sourceUrl: "https://github.com/janedoe/cv",' in js


@pytest.mark.parametrize(
    "template",
    ["index.html.j2", "sitemap.xml.j2", "site.webmanifest.j2", "template_params.js.j2"],
)
def test_minimal_inputs(tmp_path, template):
    """Test that every template renders a CV with only a name and a bare website."""
    assert _render(
        tmp_path, template, cv="cv_minimal.yaml", website="website_minimal.yaml"
    )
