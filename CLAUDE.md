# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A CV/résumé generation system that reads structured data from `cv_data.yaml` and renders it into multiple output formats (PDF via LaTeX, HTML website, sitemap, JS params, webmanifest) using Jinja2 templates. The rendered HTML site is deployed to GitHub Pages; the PDF is published as a release artifact.

## Build commands

All orchestration goes through `make`. Prefer `make` targets over direct `poetry run`, `pnpm`, `latexmk`, or `pre-commit` invocations. Python deps require Poetry inside a venv; Node deps use pnpm inside `gh-pages/`.

Prefer `make all` for full builds rather than running individual render/build targets. Use `make clear-cv` to clear the LaTeX build directory before a clean rebuild. Use `make test-renderer` to run Python tests rather than invoking `poetry run pytest` directly.

```bash
make install-deps-python      # set up .venv and install Poetry deps
make install-deps-node        # install pnpm deps for gh-pages

make render-tex               # render cv.tex from cv_data.yaml + template
make render-html              # render index.html
make render-sitemap           # render sitemap.xml
make render-js                # render template_params.js
make render-webmanifest       # render site.webmanifest

make build-cv                 # compile cv.tex → cv.pdf (requires xelatex/latexmk)
make build-website            # build Vite bundle in gh-pages/dist/
make build-release            # build everything and package release artifacts

make preview-website-dev      # start Vite dev server
make preview-website-prod     # preview the built site

make test-renderer            # run Python tests
make validate-pre-commit      # run pre-commit on all files
```

Run a single Python test:

```bash
. .venv/bin/activate && cd cv_renderer && poetry run pytest tests/test_template_utils.py::test_name -v
```

## Architecture

### Data flow

```
cv_data.yaml  →  cv_renderer (Python)  →  Jinja2 templates  →  output files
                 (validates + renders)      templates/tex/        tex/cv.tex
                                            templates/web/        gh-pages/index.html
                                                                  gh-pages/public/sitemap.xml
                                                                  gh-pages/src/template_params.js
                                                                  gh-pages/public/img/favicon/site.webmanifest
```

### Python renderer (`cv_renderer/`)

- `models.py` — Pydantic v2 models that validate `cv_data.yaml`. `MarkdownText` parses markdown fields into a mistune AST at load time; only `paragraph`, `text`, `strong`, `linebreak`, `softbreak` AST nodes are supported.
- `renderer.py` — `CVRenderer`: loads/validates data, builds Jinja2 `Environment` with custom filters and globals, renders templates.
- `ast/` — Three concrete `ASTRenderer` subclasses (`html_renderer`, `latex_renderer`, `plain_renderer`) that walk the mistune AST and emit format-specific output. The abstract base is `ast/base.py`.
- `template_type.py` — Detects output format from file extension (`.html` → HTML, `.tex`/`.latex` → LaTeX, `.xml` → XML, `.txt` → plain). Template type controls which AST renderer filters are used inside templates.
- `template_utils.py` — Helper functions exposed as Jinja2 globals: `format_current_time`, `normalize_url`, `url_path`, `dquoted`.

Jinja2 filters available in templates: `escape_latex`, `escape_html`, `markdown_latex`, `markdown_html`, `markdown_plain`.

### Jinja2 templates (`templates/`)

- `tex/cv-deedy-ng.tex.j2` — LaTeX template using the deedy-resume-ng class (`tex/deedy-resume-ng.cls`).
- `web/index.html.j2` — Main HTML template.
- `web/sitemap.xml.j2`, `web/template_params.js.j2`, `web/site.webmanifest.json.j2` — Supporting web files.

Template variables come from `CVData.model_dump()` merged with injected context (`context`, `static` dicts containing disclaimer comments and metadata).

### Website (`gh-pages/`)

Vite-based static site. Receives the rendered `index.html`, PDF, sitemap, JS params, and webmanifest as inputs before the Vite build runs.

## Code style (Python)

- Black (88-char line length), isort with black profile, flake8 with docstrings, mypy strict, bandit security scan — all enforced via pre-commit.
- Full type annotations required; mypy is configured strictly (`disallow_untyped_defs`, `warn_return_any`, etc.).

## Adding a new markdown node type

1. Add the type string to `supported_token_types` in `models.py:MarkdownText.validate_supported_markup`.
2. Add a `case` branch in `ast/base.py:ASTRenderer._render_token` and a corresponding abstract method.
3. Implement the method in all three concrete renderers (`html_renderer.py`, `latex_renderer.py`, `plain_renderer.py`).
