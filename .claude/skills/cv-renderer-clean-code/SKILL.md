---
name: cv-renderer-clean-code
description: Clean code practices specific to the cv_renderer Python package. Use when editing Python files in cv_renderer/ — especially when adding new AST token types, renderer methods, or Jinja2 filters.
paths: cv_renderer/**/*.py
---

## cv_renderer Clean Code Practices

### AST renderer pattern — no duplicate logic

All format-specific rendering (LaTeX, HTML, plain) goes through the `ASTRenderer` base class (`ast/base.py`). Never duplicate traversal logic across renderers:

- **Shared** (in base): `render_ast()`, `_render_token()`, `_render_children()`
- **Format-specific** (in each concrete renderer): one `@abstractmethod` per token type, implemented in all three

When adding a new token type, follow the CLAUDE.md checklist: `supported_token_types` → abstract method in base → implement in all three concrete renderers.

### Trust library guarantees — no redundant validation

mistune guarantees valid AST structure. Don't validate token shape or field presence. Only validate business rules (e.g. `validate_supported_markup` checks that only allowed markdown constructs appear in input data).

### On-demand rendering via Jinja2 filters

Never pre-render all formats upfront. Templates call filters (`markdown_latex`, `markdown_html`, `markdown_plain`) only when needed. Don't add eager rendering passes in `renderer.py`.

### Remove old code completely

When replacing an approach, delete the old implementation entirely — no dual-path code, no commented-out legacy methods, no `_old_`-suffixed variants.

### Only keep what's used

Methods and fields with no callers should be deleted. Pydantic models should carry only fields that templates actually access. If you're unsure, grep before keeping.
