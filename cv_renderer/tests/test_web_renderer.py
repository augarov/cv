"""Tests for the website Jinja environment and render_web."""

import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree

import jinja2
import pytest
from PIL import Image

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
SITE = Path(__file__).parents[2] / "gh-pages"
# Website files rendered by stage 1 rather than kept in gh-pages/ (the
# Makefile's WEB_FILES), relative to the site root
RENDERED_SITE_FILES = {"img/favicon/site.webmanifest", "cv.pdf", "sitemap.xml"}


def _render(tmp_path, template, cv="cv_full.yaml", website="website_full.yaml"):
    cv_path = cv if isinstance(cv, Path) else FIXTURES / cv
    website_path = website if isinstance(website, Path) else FIXTURES / website
    model = load_cv(cv_path, source_date=date(2030, 1, 2))
    output = tmp_path / "out" / template.removesuffix(".j2")
    render_web(
        model, load_website(website_path, model.cv), TEMPLATES / template, output
    )
    return output.read_text(encoding="utf-8")


class _HeadParser(HTMLParser):
    """Collect the tags of <head> in order, with their attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.title: list[str] = []
        self._in_head = False
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "head":
            self._in_head = True
        elif self._in_head:
            self.tags.append((tag, {k: v or "" for k, v in attrs}))
            self._in_title = tag == "title"

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title.append(data)


def _head(html):
    """Return the parsed <head> of a page."""
    parser = _HeadParser()
    parser.feed(html)
    return parser


def _meta(head, key, value):
    """Return the content of every <meta key=value> in the head."""
    return [
        a.get("content") for t, a in head.tags if t == "meta" and a.get(key) == value
    ]


def _site_file(path):
    """Return whether a root-relative site path is a file of the website."""
    relative = path.lstrip("/")
    return (
        relative in RENDERED_SITE_FILES
        or (SITE / relative).is_file()
        or (SITE / "public" / relative).is_file()
    )


def _image_size(path):
    """Return the width and height of an image file."""
    with Image.open(path) as image:
        return image.size


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


class TestIndexHead:
    """Test cases for the metadata in index.html's <head>."""

    @pytest.fixture
    def head(self, tmp_path):
        """Return the parsed <head> rendered from the full fixtures."""
        return _head(_render(tmp_path, "index.html.j2"))

    @pytest.fixture
    def minimal_head(self, tmp_path):
        """Return the parsed <head> of a CV with only a name and a bare website."""
        return _head(
            _render(
                tmp_path,
                "index.html.j2",
                cv="cv_minimal.yaml",
                website="website_minimal.yaml",
            )
        )

    def test_charset_first(self, head):
        """Test that <meta charset> is the first tag (within the first 1024 bytes)."""
        assert head.tags[0] == ("meta", {"charset": "UTF-8"})

    def test_one_title(self, head):
        """Test that there is exactly one <title>, the website title."""
        assert [t for t, _ in head.tags].count("title") == 1
        assert "".join(head.title) == "Jane Doe – CV"

    def test_viewport_allows_zoom(self, head):
        """Test that there is one viewport and it doesn't block zooming."""
        viewports = _meta(head, "name", "viewport")
        assert viewports == ["width=device-width, initial-scale=1.0"]

    def test_description(self, head):
        """Test that the description is the summary as plain text."""
        assert _meta(head, "name", "description") == [
            "Engineer with 10 years of experience in R&D."
        ]
        assert _meta(head, "property", "og:description") == [
            "Engineer with 10 years of experience in R&D."
        ]

    def test_canonical_and_robots(self, head):
        """Test the canonical URL and that the page may be indexed."""
        canonical = [a["href"] for t, a in head.tags if a.get("rel") == "canonical"]
        assert canonical == ["https://example.org/cv/"]
        assert _meta(head, "name", "robots") == ["index, follow"]

    def test_theme_color_matches_manifest(self, head, tmp_path):
        """Test that theme-color is the manifest's theme_color."""
        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2"))

        assert _meta(head, "name", "theme-color") == [manifest["theme_color"]]

    def test_link_previews(self, head):
        """Test the Open Graph and Twitter tags, with absolute URLs."""
        assert _meta(head, "property", "og:type") == ["profile"]
        assert _meta(head, "property", "og:url") == ["https://example.org/cv/"]
        assert _meta(head, "property", "og:title") == ["Jane Doe – CV"]
        assert _meta(head, "property", "og:site_name") == ["janedoe"]
        assert _meta(head, "property", "og:locale") == ["en_GB"]
        assert _meta(head, "property", "og:image") == [
            "https://example.org/cv/img/favicon/web-app-manifest-512x512.png"
        ]
        assert _meta(head, "name", "twitter:card") == ["summary"]

    def test_preview_image_size(self, head):
        """Test that og:image's width and height match the image."""
        path = urlparse(_meta(head, "property", "og:image")[0]).path
        image = SITE / "public" / path.removeprefix("/cv/")

        assert _image_size(image) == (
            int(_meta(head, "property", "og:image:width")[0]),
            int(_meta(head, "property", "og:image:height")[0]),
        )

    def test_local_links_exist(self, head):
        """Test that every root-relative href / src is a file of the website."""
        paths = [
            a.get("href") or a.get("src")
            for t, a in head.tags
            if t in ("link", "script")
            and (a.get("href") or a.get("src", "")).startswith("/")
            and not (a.get("href") or "").startswith("//")
        ]

        assert paths  # icons, manifest, stylesheet, script
        assert [p for p in paths if not _site_file(p)] == []

    def test_icons(self, head):
        """Test the favicon, apple-touch-icon and manifest links."""
        links = {(a.get("rel"), a.get("href")) for t, a in head.tags if t == "link"}

        assert ("icon", "/img/favicon/favicon.svg") in links
        assert ("icon", "/img/favicon/favicon.ico") in links
        assert ("apple-touch-icon", "/img/favicon/apple-touch-icon.png") in links
        assert ("manifest", "/img/favicon/site.webmanifest") in links
        assert _image_size(SITE / "public/img/favicon/apple-touch-icon.png") == (
            180,
            180,
        )

    def test_no_obsolete_shortcut_icon(self, head):
        """Test that no link uses rel="shortcut icon" (rel="icon" since HTML5)."""
        assert [a for t, a in head.tags if "shortcut" in a.get("rel", "")] == []

    def test_ico_sizes_attribute(self, head):
        """Test that the .ico link has sizes, and the .ico holds that size.

        Without sizes, Chrome may pick the .ico over the SVG.
        """
        sizes = [
            a.get("sizes")
            for t, a in head.tags
            if t == "link" and a.get("href", "").endswith(".ico")
        ]
        assert sizes == ["32x32"]
        with Image.open(SITE / "public/img/favicon/favicon.ico") as ico:
            assert (32, 32) in ico.info["sizes"]

    def test_minimal_has_every_required_tag(self, minimal_head):
        """Test that a bare website.yaml still gives the tags with defaults."""
        assert "".join(minimal_head.title) == "Jane Doe"
        assert _meta(minimal_head, "name", "description") == ["Jane Doe"]
        assert _meta(minimal_head, "property", "og:url") == ["https://example.org/cv/"]
        assert _meta(minimal_head, "property", "og:locale") == []
        assert _meta(minimal_head, "name", "theme-color") == ["#ffffff"]

    def test_markdown_in_description_is_plain(self, tmp_path):
        """Test that markdown in a description from website.yaml is removed."""
        website = tmp_path / "website.yaml"
        website.write_text(
            "url: https://example.org/cv\ndescription: '**Fast** & <safe>'\n",
            encoding="utf-8",
        )

        html = _render(tmp_path, "index.html.j2", website=website)
        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2", website=website))

        assert _meta(_head(html), "name", "description") == ["Fast & <safe>"]
        assert 'content="Fast &amp; &lt;safe&gt;"' in html
        assert manifest["description"] == "Fast & <safe>"


ICONS = SITE / "public" / "img" / "favicon"


class TestIconFiles:
    """Test cases for the icon files the page and the manifest link to."""

    def test_svg_has_viewbox(self):
        """Test that favicon.svg has a viewBox matching its size, so it scales."""
        root = ElementTree.parse(ICONS / "favicon.svg").getroot()

        assert root.get("viewBox") == f"0 0 {root.get('width')} {root.get('height')}"

    def test_ico_has_small_sizes(self):
        """Test that favicon.ico holds 16, 32 and 48 px for tabs and HiDPI tabs."""
        with Image.open(ICONS / "favicon.ico") as ico:
            assert {(16, 16), (32, 32), (48, 48)} <= ico.info["sizes"]

    @pytest.mark.parametrize(
        "name", sorted(p.name for p in ICONS.glob("*.png")), ids=str
    )
    def test_png_icons_are_opaque(self, name):
        """Test that no icon has transparent pixels.

        iOS shows transparent pixels of the apple-touch-icon as black, and a
        maskable icon must fill its whole square.
        """
        with Image.open(ICONS / name) as image:
            alpha = image.convert("RGBA").getchannel("A")
            assert alpha.getextrema() == (255, 255)


class TestWebmanifest:
    """Test cases for site.webmanifest: what browsers need to install the site."""

    @pytest.fixture
    def manifest(self, tmp_path):
        """Return the manifest rendered from the full fixtures."""
        return json.loads(_render(tmp_path, "site.webmanifest.j2"))

    def test_required_fields(self, manifest):
        """Test the fields that browsers read to install the site."""
        assert manifest["name"] == "Jane Doe – CV"
        assert manifest["short_name"] == "janedoe"
        assert manifest["description"] == "Engineer with 10 years of experience in R&D."
        assert manifest["lang"] == "en-GB"
        assert manifest["display"] == "standalone"
        assert manifest["theme_color"] == manifest["background_color"] == "#ffffff"

    @pytest.mark.parametrize(
        "url", ["https://example.org/cv", "https://example.org/cv/"]
    )
    def test_id_start_url_scope(self, tmp_path, url):
        """Test that id, start_url and scope are the site's path."""
        website = tmp_path / "website.yaml"
        website.write_text(f"url: {url}\n", encoding="utf-8")

        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2", website=website))

        assert manifest["id"] == manifest["start_url"] == manifest["scope"] == "/cv/"

    def test_site_at_domain_root(self, tmp_path):
        """Test a site at the domain root (a user's github.io site)."""
        website = tmp_path / "website.yaml"
        website.write_text("url: https://janedoe.github.io\n", encoding="utf-8")

        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2", website=website))

        assert manifest["start_url"] == manifest["scope"] == "/"
        assert manifest["icons"][0]["src"] == (
            "/img/favicon/web-app-manifest-192x192.png"
        )

    def test_icons(self, manifest):
        """Test a 192 and a 512 icon for both purposes, matching the files."""
        icons = {(i["sizes"], i["purpose"]) for i in manifest["icons"]}

        assert icons == {
            ("192x192", "any"),
            ("192x192", "maskable"),
            ("512x512", "any"),
            ("512x512", "maskable"),
        }
        for icon in manifest["icons"]:
            assert icon["type"] == "image/png"
            assert icon["src"].startswith(manifest["scope"])
            path = SITE / "public" / icon["src"].removeprefix(manifest["scope"])
            width, height = _image_size(path)
            assert f"{width}x{height}" == icon["sizes"]

    def test_non_ascii_title(self, tmp_path):
        """Test that a non-ASCII title stays valid JSON with the same text."""
        website = tmp_path / "website.yaml"
        website.write_text(
            "url: https://example.org/cv\ntitle: Žofie Dvořák – Инженер\n",
            encoding="utf-8",
        )

        manifest = json.loads(_render(tmp_path, "site.webmanifest.j2", website=website))

        assert manifest["name"] == "Žofie Dvořák – Инженер"


class TestSitemap:
    """Test cases for sitemap.xml beyond the build date."""

    NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    def test_urls_absolute_under_site(self, tmp_path):
        """Test that every <loc> is an absolute http(s) URL."""
        root = ElementTree.fromstring(
            _render(tmp_path, "sitemap.xml.j2", website="website_minimal.yaml")
        )
        locs = [e.text or "" for e in root.findall("s:url/s:loc", self.NS)]

        assert locs == ["https://example.org/cv/", "https://example.org/cv/cv.pdf"]
        assert root.tag == "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset"

    def test_lastmod_is_a_w3c_date(self, tmp_path):
        """Test that lastmod uses the W3C date format the protocol asks for."""
        root = ElementTree.fromstring(_render(tmp_path, "sitemap.xml.j2"))

        for lastmod in root.findall("s:url/s:lastmod", self.NS):
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod.text or "")

    def test_ampersand_in_url_is_escaped(self, tmp_path):
        """Test that a URL with & still gives well-formed XML."""
        website = tmp_path / "website.yaml"
        website.write_text(
            "url: https://example.org/cv/\n"
            "pdf_url: https://example.org/cv.pdf?a=1&b=2\n",
            encoding="utf-8",
        )

        xml = _render(tmp_path, "sitemap.xml.j2", website=website)
        root = ElementTree.fromstring(xml)

        assert "a=1&amp;b=2" in xml
        assert root.findall("s:url/s:loc", self.NS)[1].text == (
            "https://example.org/cv.pdf?a=1&b=2"
        )


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
