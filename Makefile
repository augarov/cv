######################################################################
#                            VARIABLES                               #
######################################################################

# Base directory
BASE_DIR = $(shell pwd)

# Directory names
WEBSITE_DIR = $(BASE_DIR)/gh-pages
RENDERER_DIR = $(BASE_DIR)/cv_renderer
TEMPLATES_DIR = $(BASE_DIR)/templates
WEB_TEMPLATES_DIR = $(TEMPLATES_DIR)/web
BUILD_DIR = $(BASE_DIR)/build
PDF_OUT_DIR = $(BUILD_DIR)/pdf
WEB_OUT_DIR = $(BUILD_DIR)/web
RELEASE_DIR = $(BUILD_DIR)/release
DOWNLOADS_DIR = $(BASE_DIR)/downloads

# Python setup
VENV_DIR = $(BASE_DIR)/.venv
PYPROJECT_TOML = $(RENDERER_DIR)/pyproject.toml
POETRY_LOCK_FILE = $(RENDERER_DIR)/poetry.lock

# Node setup
NODE_MODULES_DIR = $(WEBSITE_DIR)/node_modules
PNPM_LOCK_FILE = $(WEBSITE_DIR)/pnpm-lock.yaml
PACKAGE_JSON = $(WEBSITE_DIR)/package.json

# CV inputs. Build another CV with `make all CV_DIR=local/<name>` (local/ is
# ignored by git, for CVs that stay out of the repo).
# Only cv.yaml is required; design, locale and settings are passed when present.
# A theme override under $(CV_DIR)/<theme>/ would be a prerequisite of cv.typ.
CV_DIR ?= cv
CV_PATH = $(abspath $(CV_DIR))
CV_YAML = $(CV_PATH)/cv.yaml
WEBSITE_YAML = $(CV_PATH)/website.yaml
CV_OPTIONAL_INPUTS = design locale settings
CV_INPUTS = $(CV_YAML) \
	$(wildcard $(foreach _input,$(CV_OPTIONAL_INPUTS),$(CV_PATH)/$(_input).yaml))
CV_INPUT_FLAGS = $(strip --cv $(CV_YAML) \
	$(foreach _input,$(CV_OPTIONAL_INPUTS), \
		$(if $(wildcard $(CV_PATH)/$(_input).yaml),--$(_input) $(CV_PATH)/$(_input).yaml)))

# Build date: the last commit that changed the CV inputs, or today (empty) while
# they have uncommitted changes. Set it explicitly to override.
CV_DIRTY := $(shell git status --porcelain -- $(CV_PATH))
SOURCE_DATE_EPOCH ?= $(if $(CV_DIRTY),,$(shell git log -1 --format=%ct -- $(CV_PATH)))
# Only the renderer gets it, and only when set: other tools fail on an empty
# value (pip building a pre-commit hook: int(""))
unexport SOURCE_DATE_EPOCH

# What stage 1 renders from besides the files: the CV folder and the build date
# (today while the epoch is empty). Their stamp is removed when they change, so
# stage 1 rebuilds; the rule below writes it again.
BUILD_PARAMS := $(CV_PATH) $(or $(SOURCE_DATE_EPOCH),$(shell date +%Y-%m-%d))

# The build date, shown once per run before stage 1 renders; a notice in GitHub
# Actions. `date -d` is GNU, `date -r` BSD (macOS).
comma := ,
EPOCH_DATE = $(shell date -u -d @$(SOURCE_DATE_EPOCH) +%F 2>/dev/null || \
	date -u -r $(SOURCE_DATE_EPOCH) +%F)
BUILD_DATE_MESSAGE = $(if $(SOURCE_DATE_EPOCH), \
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) ($(EPOCH_DATE) UTC$(comma) \
	$(if $(filter file,$(origin SOURCE_DATE_EPOCH)),last commit to $(CV_DIR),set explicitly)), \
	SOURCE_DATE_EPOCH not set: the build date is today \
	($(if $(CV_DIRTY),$(CV_DIR) has uncommitted changes,no commit has changed $(CV_DIR))))
show_build_date = $(if $(BUILD_DATE_SHOWN),,$(eval BUILD_DATE_SHOWN := 1)$(info \
	$(if $(GITHUB_ACTIONS),::notice title=Build date::)$(strip $(BUILD_DATE_MESSAGE))))

# Source files from git (tracked and untracked, not ignored), so a change to the
# renderer or the site rebuilds what depends on it. Deleted files are dropped.
git_files = $(wildcard $(shell git ls-files --cached --others --exclude-standard -- $(1)))
RENDERER_SOURCES := $(call git_files,$(RENDERER_DIR)/src)
# Without the pdf.js symlink into node_modules: $(MODULES_MARKER) covers it, and
# it dangles after `make clear-all` (the list is read before the clean runs)
WEBSITE_SOURCES := $(filter-out %/public/pdfjs/build, \
	$(call git_files,$(WEBSITE_DIR)))

# Stage 1 (Python): build/pdf/ and build/web/, which has the layout of gh-pages/.
# CI: keep the paths of .github/workflows/build_cv.yaml in sync with these inputs.
OUT_TYP = $(PDF_OUT_DIR)/cv.typ
OUT_PDF = $(PDF_OUT_DIR)/cv.pdf
WEB_FILES = \
	index.html \
	public/sitemap.xml \
	src/template_params.js \
	public/img/favicon/site.webmanifest \
	public/cv.pdf
WEB_OUTPUTS = $(addprefix $(WEB_OUT_DIR)/,$(WEB_FILES))
RELEASE_OUTPUTS = $(RELEASE_DIR)/cv.pdf $(RELEASE_DIR)/gh-pages-bundle.tar.gz

# Stage 2 (Node): gh-pages/dist/ from build/web/ (copied into gh-pages/) and the
# site sources. CI: keep .github/workflows/deploy_pages.yaml in sync.
SITE_COPIES = $(addprefix $(WEBSITE_DIR)/,$(WEB_FILES))
WEBSITE_DIST = $(WEBSITE_DIR)/dist

# The pdf.js viewer in public/pdfjs/web/ is a copy of a pdf.js release; its
# library (public/pdfjs/build) links to node_modules. The versions must match.
PDFJS_VIEWER = $(WEBSITE_DIR)/public/pdfjs/web/viewer.mjs
PDFJS_PACKAGE = $(NODE_MODULES_DIR)/pdfjs-dist/package.json
CHECK_PDFJS_VERSION = \
	version=$$(node -p "require('$(PDFJS_PACKAGE)').version") && \
	grep -q "pdfjsVersion = $$version$$" $(PDFJS_VIEWER) || { \
		echo "pdfjs-dist $$version doesn't match the viewer in public/pdfjs/web/;" \
			"see .claude/skills/pdfjs-customization" >&2; exit 1; }

# CI downloads
WEBSITE_BUNDLE_ARCHIVE = $(DOWNLOADS_DIR)/gh-pages-bundle.tar.gz

# Marker files
RENDERER_STAMP                    = $(BUILD_DIR)/.renderer.stamp
BUILD_PARAMS_STAMP                = $(BUILD_DIR)/.build-params.stamp
SITE_INPUTS_STAMP                 = $(BUILD_DIR)/.site-inputs.stamp
WEBSITE_BUILD_MARKER              = $(BUILD_DIR)/.build-website.stamp
WEBSITE_BUILD_FROM_BUNDLE_MARKER  = $(BUILD_DIR)/.build-website-from-bundle.stamp
MODULES_MARKER                    = $(NODE_MODULES_DIR)/.install-deps-node.stamp
MODULES_FROZEN_MARKER             = $(NODE_MODULES_DIR)/.install-deps-node-frozen.stamp
VENV_MARKER                       = $(VENV_DIR)/.setup-env-python.stamp
PYTHON_DEPS_MARKER                = $(VENV_DIR)/.install-deps-python.stamp

ifneq ($(BUILD_PARAMS),$(shell cat $(BUILD_PARAMS_STAMP) 2>/dev/null))
$(shell rm -f $(BUILD_PARAMS_STAMP))
endif

# Commands
ACTIVATE_VENV    = . $(VENV_DIR)/bin/activate
ENTER_RENDERER_DIR = $(ACTIVATE_VENV) && cd $(RENDERER_DIR)
ENTER_WEBSITE_DIR  = cd $(WEBSITE_DIR)
RENDERER = $(ENTER_RENDERER_DIR) && \
	$(if $(SOURCE_DATE_EPOCH),SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) )poetry run python -m cv_renderer

######################################################################
#                             TARGETS                                #
######################################################################

.PHONY: all help \
        render-typst render-web \
        build-cv build-pdf build-website build-website-from-bundle build-release \
        test-renderer test-website-unit \
        install-deps-node install-deps-python install-deps-node-frozen \
        preview-website-prod preview-website-dev \
        clear-cv clear-deps-node clear-deps-python clear-all \
        validate-pre-commit

.SILENT: help

all : build-pdf build-website build-release

define PRINT_TARGET_HELP
	printf " - %-32s : %s\n"
endef

help :
	echo "Available targets:"
	$(PRINT_TARGET_HELP)   "all"                         "build PDF, website, and release"
	$(PRINT_TARGET_HELP)   "render-typst"                "render the Typst source of the PDF"
	$(PRINT_TARGET_HELP)   "build-pdf"                   "compile the PDF"
	$(PRINT_TARGET_HELP)   "build-cv"                    "alias for build-pdf"
	$(PRINT_TARGET_HELP)   "render-web"                  "render the website files into build/web"
	$(PRINT_TARGET_HELP)   "build-website"               "build website"
	$(PRINT_TARGET_HELP)   "build-website-from-bundle"   "build website from release bundle"
	$(PRINT_TARGET_HELP)   "build-release"               "build the PDF and the website bundle"
	$(PRINT_TARGET_HELP)   "test-renderer"               "run tests for renderer"
	$(PRINT_TARGET_HELP)   "test-website-unit"           "run unit tests of the website scripts"
	$(PRINT_TARGET_HELP)   "install-deps-node"           "install Node.js dependencies"
	$(PRINT_TARGET_HELP)   "install-deps-node-frozen"    "install Node.js dependencies (frozen)"
	$(PRINT_TARGET_HELP)   "install-deps-python"         "install Python dependencies with Poetry"
	$(PRINT_TARGET_HELP)   "preview-website-prod"        "preview website in production mode"
	$(PRINT_TARGET_HELP)   "preview-website-dev"         "preview website in development mode"
	$(PRINT_TARGET_HELP)   "clear-cv"                    "remove built CV files"
	$(PRINT_TARGET_HELP)   "clear-deps-node"             "remove Node.js dependencies"
	$(PRINT_TARGET_HELP)   "clear-deps-python"           "remove Python virtual environment and cache"
	$(PRINT_TARGET_HELP)   "clear-all"                   "remove all untracked files except *.local.* and local/"
	$(PRINT_TARGET_HELP)   "validate-pre-commit"         "validate pre-commit hooks"

render-typst : $(OUT_TYP)

build-pdf : $(OUT_PDF)

# Backwards-compatible alias
build-cv : build-pdf

render-web : $(WEB_OUTPUTS)

build-website : $(WEBSITE_BUILD_MARKER)

build-website-from-bundle : $(WEBSITE_BUILD_FROM_BUNDLE_MARKER)

build-release : $(RELEASE_OUTPUTS)

validate-pre-commit : $(PYTHON_DEPS_MARKER) $(MODULES_MARKER)
	$(ACTIVATE_VENV) && pre-commit run --all-files

test-renderer : $(PYTHON_DEPS_MARKER)
	$(ENTER_RENDERER_DIR) && poetry run pytest

test-website-unit : $(MODULES_MARKER)
	$(ENTER_WEBSITE_DIR) && pnpm run test:unit

install-deps-node : $(MODULES_MARKER)

install-deps-node-frozen : $(MODULES_FROZEN_MARKER)

install-deps-python : $(PYTHON_DEPS_MARKER)

preview-website-prod : $(WEBSITE_BUILD_MARKER)
	$(ENTER_WEBSITE_DIR) && pnpm run preview

preview-website-dev : $(SITE_INPUTS_STAMP) $(MODULES_MARKER)
	$(ENTER_WEBSITE_DIR) && pnpm run dev

clear-cv :
	rm -rf $(BUILD_DIR)
	rm -f $(SITE_COPIES)
	rm -rf $(WEBSITE_DIST)

clear-deps-node :
	rm -rf $(WEBSITE_DIR)/node_modules
	rm -f $(MODULES_MARKER)
	rm -f $(MODULES_FROZEN_MARKER)

clear-deps-python :
	rm -rf $(VENV_DIR)
	rm -f $(PYTHON_DEPS_MARKER)
	rm -rf __pycache__
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

clear-all :
	# Keeps local files such as *.local.md, .claude/settings.local.json and local/
	git clean -xdf -e '*.local.*' -e '/local/'

######################################################################
#                           BUILD RULES                              #
######################################################################

# ── Stage 1: renderer ─────────────────────────────────────────────────────

# Any change to the renderer or its dependencies (including rendercv's own Typst
# templates) rebuilds all of stage 1
$(RENDERER_STAMP) : $(RENDERER_SOURCES) $(PYTHON_DEPS_MARKER)
	mkdir -p $(@D)
	touch $@

$(BUILD_PARAMS_STAMP) :
	mkdir -p $(@D)
	echo '$(BUILD_PARAMS)' > $@

# ── Stage 1: PDF ──────────────────────────────────────────────────────────

$(OUT_TYP) : $(CV_INPUTS) $(RENDERER_STAMP) $(BUILD_PARAMS_STAMP)
	$(show_build_date)$(RENDERER) typst $(CV_INPUT_FLAGS) --output $@

$(OUT_PDF) : $(OUT_TYP) $(RENDERER_STAMP)
	$(RENDERER) pdf --input $< --output $@

# ── Stage 1: website files ────────────────────────────────────────────────

# $(1) = template, $(2) = output
define WEB_RULE
$(2) : $(1) $(CV_INPUTS) $(WEBSITE_YAML) $(RENDERER_STAMP) $(BUILD_PARAMS_STAMP)
	$$(show_build_date)$$(RENDERER) web $$(CV_INPUT_FLAGS) --website $$(WEBSITE_YAML) --template $$< --output $$@
endef
$(eval $(call WEB_RULE,$(WEB_TEMPLATES_DIR)/index.html.j2,$(WEB_OUT_DIR)/index.html))
$(eval $(call WEB_RULE,$(WEB_TEMPLATES_DIR)/sitemap.xml.j2,$(WEB_OUT_DIR)/public/sitemap.xml))
$(eval $(call WEB_RULE,$(WEB_TEMPLATES_DIR)/template_params.js.j2,$(WEB_OUT_DIR)/src/template_params.js))
$(eval $(call WEB_RULE,$(WEB_TEMPLATES_DIR)/site.webmanifest.j2,$(WEB_OUT_DIR)/public/img/favicon/site.webmanifest))

$(WEB_OUT_DIR)/public/cv.pdf : $(OUT_PDF)
	mkdir -p $(@D)
	cp $< $@

# ── Stage 1: release (the hand-off to stage 2) ────────────────────────────

$(RELEASE_DIR)/cv.pdf : $(OUT_PDF)
	mkdir -p $(@D)
	cp $< $@

$(RELEASE_DIR)/gh-pages-bundle.tar.gz : $(WEB_OUTPUTS)
	mkdir -p $(@D)
	tar -czf $@ -C $(WEB_OUT_DIR) $(WEB_FILES)

# ── Stage 2: website ──────────────────────────────────────────────────────

$(SITE_INPUTS_STAMP) : $(WEB_OUTPUTS)
	cp -R $(WEB_OUT_DIR)/. $(WEBSITE_DIR)/
	touch $@

$(WEBSITE_BUILD_MARKER) : $(SITE_INPUTS_STAMP) $(WEBSITE_SOURCES) $(MODULES_MARKER)
	$(CHECK_PDFJS_VERSION)
	$(ENTER_WEBSITE_DIR) && pnpm run build
	touch $@

# CI: unpack the release bundle into build/web/ instead of running stage 1, then
# the same steps as above (no prerequisites on stage 1, which CI doesn't run here)
$(WEBSITE_BUILD_FROM_BUNDLE_MARKER) : $(WEBSITE_BUNDLE_ARCHIVE) $(WEBSITE_SOURCES) $(MODULES_FROZEN_MARKER)
	rm -rf $(WEB_OUT_DIR)
	mkdir -p $(WEB_OUT_DIR)
	tar -xzf $< -C $(WEB_OUT_DIR)
	cp -R $(WEB_OUT_DIR)/. $(WEBSITE_DIR)/
	$(CHECK_PDFJS_VERSION)
	$(ENTER_WEBSITE_DIR) && pnpm run build
	touch $@

# ── Python / Node deps ────────────────────────────────────────────────────

$(MODULES_MARKER) : $(PACKAGE_JSON)
	$(ENTER_WEBSITE_DIR) && pnpm install
	touch $(MODULES_MARKER)

$(MODULES_FROZEN_MARKER) : $(PACKAGE_JSON) $(PNPM_LOCK_FILE)
	$(ENTER_WEBSITE_DIR) && pnpm install --frozen-lockfile
	touch $(MODULES_FROZEN_MARKER)
	touch $(MODULES_MARKER)

$(PYTHON_DEPS_MARKER) : $(VENV_MARKER) $(PYPROJECT_TOML) $(POETRY_LOCK_FILE)
	$(ENTER_RENDERER_DIR) && poetry install
	touch $(PYTHON_DEPS_MARKER)

$(VENV_MARKER) :
	python3 -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install poetry
	touch $(VENV_MARKER)
