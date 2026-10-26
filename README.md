# Curriculum Vitae / Résumé

[![Validate & Test](https://github.com/augarov/cv/actions/workflows/validate.yaml/badge.svg)](https://github.com/augarov/cv/actions/workflows/validate.yaml)
[![Build CV](https://github.com/augarov/cv/actions/workflows/build_cv.yaml/badge.svg)](https://github.com/augarov/cv/actions/workflows/build_cv.yaml)
[![Build & deploy GitHub Pages](https://github.com/augarov/cv/actions/workflows/deploy_pages.yaml/badge.svg)](https://github.com/augarov/cv/actions/workflows/deploy_pages.yaml)

### Links

[Online preview](https://augarov.github.io/cv/)

[Download latest build](https://github.com/augarov/cv/releases/download/cv-latest/cv.pdf)

### Build

The CV is written in [rendercv](https://docs.rendercv.com/)'s YAML format in `cv/`; rendercv renders the PDF with Typst, and the same data renders the website.

Requirements: Python 3.12 and, for the website, Node.js with pnpm.

```bash
make all                    # PDF in build/pdf/, website in gh-pages/dist/, release in build/release/
make build-pdf              # the PDF only
make preview-website-prod   # serve the built website
make all CV_DIR=other-cv    # build the CV in another folder
```

The minimal inputs:

- **PDF:** `cv.yaml` alone. `design.yaml`, `locale.yaml` and `settings.yaml` are optional and replace rendercv's defaults (the `classic` theme, English).
- **Website:** also `website.yaml`, with at least the site's `url`:

  ```yaml
  url: https://example.github.io/cv/
  ```

  The title, author and PDF link default from the CV and the URL; `source_url`, `keywords` and `locale` are optional.

`make help` lists all targets.
