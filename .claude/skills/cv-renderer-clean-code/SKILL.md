---
name: cv-renderer-clean-code
description: Clean code practices specific to the cv_renderer Python package. Use when editing Python files in cv_renderer/ — especially when adding Jinja2 filters, CLI options, or new imports from rendercv.
paths: cv_renderer/**/*.py
---

## cv_renderer Clean Code Practices

### rendercv does the CV, we do the website

rendercv owns the schema, validation and the PDF (Typst). Don't re-implement any of it: no own CV models, no own date formatting, no own Typst templating. Our code covers what rendercv doesn't: loading the inputs with good errors, the `Website` model, the website's Jinja environment and its filters.

### Keep the rendercv surface small

rendercv has no documented Python API, so every import from it is internal. Each import lives in one module (listed in CLAUDE.md) and is checked by `tests/unit/test_rendercv_contract.py`. A new import, or a template relying on a model attribute beyond the plain schema, gets a contract test in the same change.

### Trust library guarantees — no redundant validation

rendercv validates the CV, pydantic validates `website.yaml`, and `markdown-it-py` escapes raw HTML (`html: False`). Don't re-check what they guarantee. Validate only what they can't know (e.g. a design file must contain a `design:` section).

### Convert at render time, in filters

Templates get the raw, validated model. Markdown, dates and phone numbers are converted by filters (`markdown`, `markdown_plain`, `date_range`, `single_date`, `phone_display`) where they're used, because one field can land in HTML, an attribute or JSON, each with its own conversion and escaping. Don't add pre-rendering passes over the model, and don't use rendercv's processed (`process_model`) model for the website.

### Errors name the file

Every input problem becomes an `InputError` whose message starts with the file (and line/column when known). `app.run` logs it as one line and returns 1; no tracebacks for user errors.

### Remove old code completely

When replacing an approach, delete the old implementation entirely — no dual-path code, no commented-out legacy methods, no `_old_`-suffixed variants.

### Only keep what's used

Functions, filters and fields with no callers should be deleted. The `Website` model carries only fields that templates actually access. If you're unsure, grep before keeping.
