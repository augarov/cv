---
name: makefile-conventions
description: Conventions for editing the project Makefile or adding new make targets. Use when asked to add, rename, or restructure make targets or variables.
paths: Makefile
---

## Makefile Conventions

The Makefile must work with GNU Make 3.81 (macOS): no grouped targets (`&:` needs Make 4.3).

### Target naming: kebab-case, action-component pattern

```makefile
build-pdf              # verb-noun
install-deps-python    # verb-noun-qualifier
clear-deps-node
render-typst
preview-website-dev
```

### Variable naming

- Directories: `*_DIR` (e.g. `BUILD_DIR`, `VENV_DIR`, `WEBSITE_DIR`)
- Files: descriptive name or `*_FILE`
- Stamps of build steps: `*_STAMP`; markers of installed dependencies: `*_MARKER`
- Always build paths from `BASE_DIR = $(shell pwd)` — never hardcode absolute paths. A path given by the user (`CV_DIR`) goes through `$(abspath …)`, because recipes `cd` into `cv_renderer/`.

### Build rules

- **One rule, one output.** Each recipe writes exactly one file.
- **Prerequisites are exactly what the recipe reads**, and the recipe takes its paths from them: `$<` for the input, `$@` for the output. Repeated rules of one shape use a `define` + `$(eval $(call …))` (with `$$<` / `$$@` inside the `define`).
- **Fixed inputs are listed explicitly** (templates, YAML files). File sets that change with the code come from git: `$(call git_files,<dir>)` (tracked and untracked, not ignored, deleted files dropped).
- **Outputs depend on the tool.** Stage 1 outputs depend on `$(RENDERER_STAMP)`, which depends on the renderer sources and the Python dependencies.
- **Values are inputs too.** Stage 1 outputs depend on `$(BUILD_PARAMS_STAMP)`, which holds `CV_PATH` and the build date and is removed at parse time when they change. Add any other variable that changes the output to `BUILD_PARAMS`.
- Optional inputs are prerequisites and flags only when they exist (`$(wildcard …)`).
- Stage 1 (Python) writes `build/pdf/` and `build/web/`; stage 2 (Node) builds `gh-pages/dist/` from `build/web/`. Keep the `paths` of `.github/workflows/build_cv.yaml` (push and pull_request) in sync with the inputs of both stages. It's the only workflow that runs on push and calls `deploy_pages.yaml` (stage 2), which has no push trigger, so a push never starts two deploys.

### .PHONY declaration

All non-file targets must be listed in `.PHONY`, and in the `help` target.

### Marker files for single-shot targets

Use hidden `.stamp` files to prevent re-running expensive setup operations:

```makefile
PYTHON_DEPS_MARKER = $(VENV_DIR)/.install-deps-python.stamp

$(PYTHON_DEPS_MARKER) : $(PYPROJECT_TOML) $(UV_LOCK_FILE) $(PYTHON_VERSION_FILE)
	$(ENTER_RENDERER_DIR) && uv sync --locked
	touch $(PYTHON_DEPS_MARKER)
```

Setup markers take the tool check of their stage as an order-only prerequisite (`| check-deps-python`, `| check-deps-node`): the phony check runs once per make run before anything that uses the tools, and never makes the marker out of date. A new tool goes into `scripts/check-deps.sh` (its minimum read from the project file that defines it), not into a recipe.

### File organization order

1. Section: VARIABLES (with `######` banner comments)
2. Section: TARGETS (`.PHONY`, `all`, `help`, the phony targets)
3. Section: BUILD RULES (file-producing rules, grouped by stage)
