"""Tests for the command line."""

from pathlib import Path

import pytest

from cv_renderer.app import run
from cv_renderer.app_params import make_parser

FIXTURES = Path(__file__).parent / "fixtures"
CV = str(FIXTURES / "cv_full.yaml")
WEBSITE = str(FIXTURES / "website_full.yaml")


@pytest.fixture(autouse=True)
def no_source_date(monkeypatch):
    """Keep the environment's SOURCE_DATE_EPOCH out of the tests."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)


class TestParser:
    """Test cases for make_parser."""

    def test_typst(self):
        """Test that typst takes the CV inputs and an output."""
        args = make_parser().parse_args(
            ["typst", "--cv", "a.yaml", "--design", "d.yaml", "-o", "cv.typ"]
        )

        assert args.cv == Path("a.yaml")
        assert args.design == Path("d.yaml")
        assert args.locale is None
        assert args.settings is None
        assert args.output == Path("cv.typ")

    def test_pdf(self):
        """Test that pdf takes an input and an output."""
        args = make_parser().parse_args(["pdf", "-i", "cv.typ", "-o", "cv.pdf"])

        assert (args.input, args.output) == (Path("cv.typ"), Path("cv.pdf"))

    def test_web(self):
        """Test that web takes the CV inputs, website, template and output."""
        args = make_parser().parse_args(
            ["web", "--cv", "a.yaml", "--website", "w.yaml"]
            + ["--template", "t.html.j2", "-o", "index.html"]
        )

        assert args.website == Path("w.yaml")
        assert args.template == Path("t.html.j2")

    @pytest.mark.parametrize(
        "argv",
        [
            ["typst", "--cv", "a.yaml", "--website", "w.yaml", "-o", "x"],
            ["typst", "-o", "x"],
            ["typst", "--cv", "a.yaml", "--type", "typst", "-o", "x"],
            ["typst", "--cv", "a.yaml", "--force", "-o", "x"],
            ["pdf", "-i", "x"],
            ["web", "--cv", "a.yaml", "--template", "t", "-o", "x"],
            ["web", "--cv", "a.yaml", "--website", "w", "-o", "x"],
            ["render", "--cv", "a.yaml"],
        ],
    )
    def test_invalid_arguments(self, argv):
        """Test unknown or missing options give an argparse error."""
        with pytest.raises(SystemExit) as error:
            make_parser().parse_args(argv)

        assert error.value.code == 2


class TestRun:
    """Test cases for run."""

    def test_typst_and_web(self, tmp_path):
        """Test that typst and web run end to end on the fixtures."""
        typ, html = tmp_path / "cv.typ", tmp_path / "web" / "page.html"
        template = tmp_path / "page.html.j2"
        template.write_text("{{ cv.name }} {{ website.url }}", encoding="utf-8")

        assert run(["-s", "typst", "--cv", CV, "-o", str(typ)]) == 0
        assert (
            run(
                ["-s", "web", "--cv", CV, "--website", WEBSITE]
                + ["--template", str(template), "-o", str(html)]
            )
            == 0
        )

        assert "Jane Doe" in typ.read_text(encoding="utf-8")
        assert html.read_text(encoding="utf-8") == "Jane Doe https://example.org/cv/"

    @pytest.mark.parametrize(
        "argv, missing",
        [
            (["typst", "--cv", "{tmp}/no.yaml", "-o", "{tmp}/cv.typ"], "no.yaml"),
            (
                ["typst", "--cv", CV, "--design", "{tmp}/no.yaml", "-o", "{tmp}/x"],
                "no.yaml",
            ),
            (["pdf", "-i", "{tmp}/no.typ", "-o", "{tmp}/cv.pdf"], "no.typ"),
            (
                ["web", "--cv", CV, "--website", "{tmp}/no.yaml"]
                + ["--template", "{tmp}/t.html.j2", "-o", "{tmp}/x"],
                "no.yaml",
            ),
            (
                ["web", "--cv", CV, "--website", WEBSITE]
                + ["--template", "{tmp}/no.html.j2", "-o", "{tmp}/x"],
                "no.html.j2",
            ),
        ],
    )
    def test_missing_file(self, tmp_path, capsys, argv, missing):
        """Test that a missing file gives exit code 1 and one line naming it."""
        argv = [arg.replace("{tmp}", str(tmp_path)) for arg in argv]

        assert run(["-l", "ERROR", *argv]) == 1

        lines = capsys.readouterr().err.strip().splitlines()
        assert len(lines) == 1
        assert str(tmp_path / missing) in lines[0]

    def test_invalid_source_date_epoch(self, tmp_path, monkeypatch):
        """Test that an invalid SOURCE_DATE_EPOCH fails the build."""
        monkeypatch.setenv("SOURCE_DATE_EPOCH", "yesterday")

        assert run(["-s", "typst", "--cv", CV, "-o", str(tmp_path / "x")]) == 1
