"""Tests that the real CVs build: cv/ and, on a local checkout, each local/<name>/."""

from pathlib import Path

import pytest

from cv_renderer.app import run

ROOT = Path(__file__).parents[2]
TEMPLATES = ROOT / "templates" / "web"
OPTIONAL_INPUTS = ["design", "locale", "settings"]
CV_DIRS = [ROOT / "cv"] + sorted(
    folder for folder in (ROOT / "local").glob("*") if (folder / "cv.yaml").is_file()
)


@pytest.mark.slow
@pytest.mark.parametrize("cv_dir", CV_DIRS, ids=lambda d: str(d.relative_to(ROOT)))
def test_cv_builds(cv_dir, tmp_path):
    """Test that the Typst source, the PDF and all web templates render."""
    cv_inputs = ["--cv", str(cv_dir / "cv.yaml")]
    for name in OPTIONAL_INPUTS:
        if (cv_dir / f"{name}.yaml").is_file():
            cv_inputs += [f"--{name}", str(cv_dir / f"{name}.yaml")]

    typ, pdf = tmp_path / "cv.typ", tmp_path / "cv.pdf"
    assert run(["-s", "typst", *cv_inputs, "--output", str(typ)]) == 0
    assert run(["-s", "pdf", "--input", str(typ), "--output", str(pdf)]) == 0
    assert pdf.read_bytes().startswith(b"%PDF")

    templates = sorted(TEMPLATES.glob("*.j2"))
    assert len(templates) == 4
    for template in templates:
        output = tmp_path / template.stem
        web = ["--website", str(cv_dir / "website.yaml")]
        web += ["--template", str(template), "--output", str(output)]
        assert run(["-s", "web", *cv_inputs, *web]) == 0
        assert output.read_text(encoding="utf-8").strip()
