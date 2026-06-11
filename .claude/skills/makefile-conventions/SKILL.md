---
name: makefile-conventions
description: Conventions for editing the project Makefile or adding new make targets. Use when asked to add, rename, or restructure make targets or variables.
paths: Makefile
---

## Makefile Conventions

### Target naming: kebab-case, action-component pattern

```makefile
build-cv               # verb-noun
install-deps-python    # verb-noun-qualifier
clear-deps-node
render-tex
preview-website-dev
```

### Variable naming

- Directories: `*_DIR` (e.g. `TEX_DIR`, `VENV_DIR`, `GHPAGES_DIR`)
- Files: descriptive name or `*_FILE`
- Marker stamps: `*_MARKER`
- Always build paths from `BASE_DIR = $(shell pwd)` — never hardcode absolute paths

### .PHONY declaration

All non-file targets must be listed in `.PHONY` at the top of the file.

### Marker files for single-shot targets

Use hidden `.stamp` files to prevent re-running expensive setup operations:

```makefile
VENV_MARKER = $(VENV_DIR)/.setup-env-python.stamp

setup-env-python : $(VENV_MARKER)
$(VENV_MARKER) :
	python3 -m venv $(VENV_DIR)
	touch $(VENV_MARKER)
```

### File organization order

1. `.PHONY` declaration
2. Section: VARIABLES (with `######` banner comments)
3. Section: TARGETS (`all`, `help`)
4. Section: BUILD RULES (file-producing targets)
