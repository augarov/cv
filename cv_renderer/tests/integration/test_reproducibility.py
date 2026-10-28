"""Tests that the same inputs and source date give byte-identical outputs."""

from pathlib import Path

from cv_renderer.app import run

FIXTURES = Path(__file__).parents[1] / "fixtures"
TEMPLATES = Path(__file__).parents[3] / "templates" / "web"
SOURCE_DATE_EPOCH = "1893542400"  # 2030-01-02 UTC
WEB_OUTPUTS = {"index.html": "index.html.j2", "sitemap.xml": "sitemap.xml.j2"}
OUTPUTS = ["cv.typ", "cv.pdf", *WEB_OUTPUTS]


def _build(folder: Path) -> None:
    settings = folder / "settings.yaml"
    settings.write_text("settings:\n  pdf_title: Jane Doe CV\n", encoding="utf-8")
    cv_inputs = [
        "--cv",
        str(FIXTURES / "cv_full.yaml"),
        "--design",
        str(FIXTURES / "design.yaml"),
        "--locale",
        str(FIXTURES / "locale.yaml"),
        "--settings",
        str(settings),
    ]
    typ, pdf = folder / "cv.typ", folder / "cv.pdf"
    assert run(["-s", "typst", *cv_inputs, "--output", str(typ)]) == 0
    assert run(["-s", "pdf", "--input", str(typ), "--output", str(pdf)]) == 0
    for output, template in WEB_OUTPUTS.items():
        web = ["--website", str(FIXTURES / "website_full.yaml")]
        web += ["--template", str(TEMPLATES / template)]
        web += ["--output", str(folder / output)]
        assert run(["-s", "web", *cv_inputs, *web]) == 0


def test_same_source_date_gives_identical_outputs(tmp_path, monkeypatch):
    """Test that two builds in different folders are byte-identical."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()

    _build(first)
    _build(second)

    for name in OUTPUTS:
        assert (first / name).read_bytes() == (second / name).read_bytes(), name
    sitemap = (first / "sitemap.xml").read_text(encoding="utf-8")
    assert sitemap.count("<lastmod>2030-01-02</lastmod>") == 2
