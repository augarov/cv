# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A CV/résumé build. The CV data is in [rendercv](https://github.com/rendercv/rendercv)'s YAML schema in `cv/`. rendercv, used as a Python library, validates it and renders the PDF through Typst. The same validated model feeds our own Jinja2 templates for the GitHub Pages website (HTML, sitemap, JS params, webmanifest). The website is deployed to GitHub Pages; the PDF and the website bundle are published as a release.

## Build commands

All orchestration goes through `make`. Prefer `make` targets over direct `uv`, `pnpm`, or `pre-commit` invocations. Python deps are managed by uv (`cv_renderer/uv.lock`) in the root `.venv`, with the Python of `cv_renderer/.python-version` (3.14), which uv installs itself; uv's cache and Pythons are in the repo (`.uv-cache/`, `.uv-python/`, ignored). The Makefile sets the `UV_*` variables for this, so a bare `uv run` in `cv_renderer/` would create a second venv: go through `make`, or activate `.venv`. Node deps use pnpm inside `gh-pages/`.

Prefer `make all` for full builds rather than running individual targets. Use `make clear-cv` to remove the build outputs before a clean rebuild. Use `make test-renderer` (all), `make test-renderer-unit` or `make test-renderer-integration` to run Python tests rather than invoking `pytest` directly.

```bash
make install-deps-python      # uv sync: .venv with Python and the locked deps
make install-deps-node        # install pnpm deps for gh-pages

make render-typst             # build/pdf/cv.typ
make build-pdf                # build/pdf/cv.pdf (alias: build-cv)
make render-web               # the website files in build/web/
make build-website            # copy build/web/ into gh-pages/, build gh-pages/dist/
make build-release            # build/release/: cv.pdf + gh-pages-bundle.tar.gz
make all                      # all of the above
make clear-cv                 # remove build/ and the copies in gh-pages/

make preview-website-dev      # start Vite dev server
make preview-website-prod     # preview the built site

make test-renderer            # run all Python tests: unit, then integration
make test-renderer-unit       # Python unit tests (tests/unit/, on the fixtures)
make test-renderer-integration # whole builds through the CLI (tests/integration/): cv/, local/*/, reproducibility
make test-website-unit        # website script units (node --test)
make test-website-dist        # checks of the built files in gh-pages/dist/ (no browser)
make test-website-e2e         # browser tests (Playwright) on the built site; E2E_ARGS="--project=firefox"
make install-playwright-browsers # Chromium, Firefox, WebKit into .playwright-browsers/ (once per Playwright version)
make validate-pre-commit      # run pre-commit on all files
make check-deps-python        # git, uv (also check-deps-node: git, git-lfs, Node.js, pnpm; check-deps: both)
```

- `make all CV_DIR=local/<name>` builds the CV in another folder (default `cv`). `local/` is ignored by git: CVs there never go into the repo.
- `SOURCE_DATE_EPOCH` sets the build date of the PDF and the website (an explicit `settings.current_date` wins). The Makefile sets it to the last commit that changed `CV_DIR`, or leaves it empty (today) while `CV_DIR` has uncommitted changes. Before stage 1 renders, make prints which date it uses and why (a `::notice` annotation in GitHub Actions). The same inputs and date give byte-identical `build/pdf/` and `build/web/` files (not the release tarball, whose gzip header and file times differ).
- `PREVIEW_HOST` sets the address the `preview-website-*` servers listen on (default `127.0.0.1`); `make preview-website-prod PREVIEW_HOST=0.0.0.0` makes them reachable through a forwarded port.
- Browser tests: `gh-pages/playwright.config.js` serves `dist/` with `vite preview` on port 4174 under the base path and runs `gh-pages/tests/e2e/*.spec.js` in five projects (chromium, firefox, webkit, pixel, iphone). Expected values come from the built files (`tests/dist/helpers.js`), so they pass for any CV. Browsers live in `.playwright-browsers/` (`PLAYWRIGHT_BROWSERS_PATH`); CI caches them by Playwright version and installs their system libraries (`PLAYWRIGHT_INSTALL_FLAGS=--with-deps`), runs them before the Pages upload (a failure blocks the deploy and fails a PR) and uploads the HTML report when they fail. On Linux, a new machine needs the libraries once: `sudo gh-pages/node_modules/.bin/playwright install-deps`.
- `make help` lists all targets.
- `scripts/check-deps.sh python|node` checks that a stage's tools are installed and new enough, with an install hint per problem. The dependency markers take `check-deps-python` / `check-deps-node` as order-only prerequisites, so every target checks its own stage's tools first (CI's stage 2 job has no Python and checks only Node). The minimums live in the project files: uv's in `cv_renderer/pyproject.toml` (`tool.uv.required-version`), Node.js' and pnpm's in `gh-pages/package.json` (`engines`, which pnpm enforces too); the script only reads `>=X.Y.Z`. The exact pnpm is `packageManager` there: pnpm switches to it locally, and CI's `pnpm/action-setup` installs it. CI's Node.js major is `node-version` in `validate.yaml` and `deploy_pages.yaml`.
- `.github/dependabot.yml` opens monthly version-update PRs (uv, npm, GitHub Actions, pre-commit hook `rev`s), one grouped PR per ecosystem; for uv, npm and pre-commit, each major update gets its own PR. uv updates change only `uv.lock` while `pyproject.toml`'s range allows them (`versioning-strategy: increase-if-necessary`). `tool.uv.required-version` stays at Dependabot's uv (0.13.5), else its uv updates fail. `pdfjs-dist` is ignored (the viewer is upgraded with it by hand), and rendercv gets patch updates only.

Run a single Python test:

```bash
. .venv/bin/activate && cd cv_renderer && pytest tests/unit/test_template_utils.py::test_name -v
```

## Architecture

### Inputs (`cv/`)

| File            | Required?                       | Content                                                                                        |
| --------------- | ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `cv.yaml`       | yes                             | rendercv's `cv:` section; custom themes resolve relative to this file (no `photo` support yet) |
| `design.yaml`   | no (rendercv's `classic` theme) | rendercv's `design:` section                                                                   |
| `locale.yaml`   | no (English)                    | rendercv's `locale:` section                                                                   |
| `settings.yaml` | no (rendercv's defaults)        | rendercv's `settings:` section                                                                 |
| `website.yaml`  | only for the website            | `Website` model (`models.py`); only `url` is required, the rest defaults from `url` and the CV |

A separate `design.yaml` / `locale.yaml` / `settings.yaml` replaces the section of the same name inside `cv.yaml` (no merge); the renderer warns when both exist.

### Data flow: two stages

```
Stage 1 (Python, cv_renderer)                       Stage 2 (Node, gh-pages/)
cv/*.yaml → rendercv model ─┬→ typst → build/pdf/cv.typ → pdf → build/pdf/cv.pdf
                            └→ web + templates/web/*.j2 → build/web/  ──copy──→ gh-pages/ → Vite → gh-pages/dist/
build/release/ = cv.pdf + gh-pages-bundle.tar.gz (tar of build/web/), the hand-off between the stages
```

`build/web/` has the layout of `gh-pages/` (`index.html`, `src/template_params.js`, `public/sitemap.xml`, `public/img/favicon/site.webmanifest`, `public/cv.pdf`). CI uses the same split: `build_cv.yaml` runs stage 1 and uploads the release, `deploy_pages.yaml` downloads the bundle by tag (`make build-website-from-bundle`) and deploys. On a pull request (stage 1 or stage 2 inputs), `build_cv.yaml` uploads `build/release/` as the workflow artifact `cv-build` instead of releasing, and `deploy_pages.yaml` builds the website from that artifact without deploying. Only `build_cv.yaml` runs on push and pull request; `deploy_pages.yaml` has no push trigger, so a push gives one deploy. Keep `build_cv.yaml`'s `paths` in sync with the inputs of both stages in the Makefile.

### Python renderer (`cv_renderer/`)

CLI (`python -m cv_renderer`), one subcommand per kind of processing:

```
cv_renderer typst --cv cv/cv.yaml [--design …] [--locale …] [--settings …] --output build/pdf/cv.typ
cv_renderer pdf   --input build/pdf/cv.typ --output build/pdf/cv.pdf
cv_renderer web   --cv cv/cv.yaml [--design …] [--locale …] [--settings …] --website cv/website.yaml \
                  --template templates/web/index.html.j2 --output build/web/index.html
```

- `app.py` / `app_params.py` — argument parsing and dispatch; errors are logged as one line and exit with status 1.
- `inputs.py` — `load_cv` (rendercv's YAML files → `RenderCVModel`) and `load_website`. Every input problem becomes an `InputError` whose message names the file (and line/column where rendercv knows it).
- `build_date.py` — the build date from `SOURCE_DATE_EPOCH` / `settings.current_date`, the same for the PDF and the website.
- `typst_renderer.py` — the Typst source via rendercv's `render_full_template`.
- `pdf_builder.py` — compiles `.typ` to PDF with `typst-py`, rendercv's Typst package and `rendercv_fonts`.
- `web_renderer.py` — our own Jinja environment for `templates/web/`: autoescape for `.html.j2` / `.xml.j2`, `StrictUndefined`, `tojson` for JS/JSON templates. Templates get `cv`, `design`, `locale` (the raw rendercv model), `website` and `build_date`.
- `template_utils.py` — the template filters: `markdown` (inline HTML via `markdown-it-py`, raw HTML escaped), `markdown_plain`, `date_range` / `single_date` (rendercv's date functions, same formats as the PDF), `phone_display`, `as_list`; global `url_path`.
- `models.py` — the `Website` model.

The website renders the raw, validated model, not rendercv's processed one, and converts markdown and dates in filters at render time, so each output (HTML body, `<meta>`, JSON) gets its own conversion and escaping. With `StrictUndefined`, check fields that only some entry types have with `is defined`. `index.html.j2` has one macro per section key it knows (`section_macros`) and renders them in `cv.yaml`'s order, like the PDF; other keys are left out.

### rendercv as a dependency

rendercv has no documented Python API, so every import from it is internal. It's pinned to `>=2.8,<2.9` (patch updates only); an upgrade is a deliberate step. Imports are limited to: `build_rendercv_dictionary` / `build_rendercv_model_from_commented_map` and `rendercv.exception` (`inputs.py`), `render_full_template` (`typst_renderer.py`), `get_package_path` (`pdf_builder.py`), `format_date_range` / `format_single_date` (`template_utils.py`), and the schema models for type hints. `tests/unit/test_rendercv_contract.py` checks each of these, plus the model attributes the templates rely on (`SocialNetwork.url`, `cv.phone` as a `tel:` URI, `PublicationEntry.doi_url`). Add any new import or relied-on attribute there.

### Website (`gh-pages/`)

Vite-based static site. Receives the rendered files from `build/web/` before the Vite build runs. The PDF is shown with a customized pdf.js viewer (`gh-pages/public/pdfjs/`); the website build fails when the installed `pdfjs-dist` isn't the viewer's version (`scripts/check-pdfjs-version.sh`). Vite copies the viewer as is; `vite-plugins/pdfjs-viewer.js` then minifies it in `dist/pdfjs/` and deletes the files it never loads (source maps, unminified builds, sandbox, debugger, other locales).

## Code style (Python)

- Ruff (`[tool.ruff]` in `cv_renderer/pyproject.toml`): `ruff format` (black's style, 88-char lines) and `ruff check` with pyflakes, pycodestyle, pep257 docstrings and isort's import order; mypy strict; bandit security scan — all enforced via pre-commit.
- The Ruff and mypy hooks run `.venv/bin/ruff` / `.venv/bin/mypy` from the project venv: their versions come from `uv.lock` (no hook `rev` to keep in sync), and mypy sees the installed packages' type hints, checking `src/` and `tests/`. Run `make install-deps-python` first, also in a new worktree; otherwise the hooks fail with "executable not found".
- Full type annotations required; mypy is configured strictly (`disallow_untyped_defs`, `warn_return_any`, etc.).

## Adding a website filter

1. Add the function to `template_utils.py`, with tests in `tests/unit/test_template_utils.py`.
2. Register it in `web_renderer.py:make_web_environment`.
3. Mark HTML output as safe (`Markup`) only after escaping its input.
