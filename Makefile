######################################################################
#                            VARIABLES                               #
######################################################################

# Base directory
BASE_DIR = $(shell pwd)

# Directory names
TEX_DIR = $(BASE_DIR)/tex
WEBSITE_DIR = $(BASE_DIR)/gh-pages
RENDERER_DIR = $(BASE_DIR)/cv_renderer
TEMPLATES_DIR = $(BASE_DIR)/templates
BUILD_DIR = $(BASE_DIR)/build
RELEASE_DIR = $(BUILD_DIR)/release
WEBSITE_BUNDLE_DIR = $(BUILD_DIR)/gh-pages-bundle
DOWNLOADS_DIR = $(BASE_DIR)/downloads

# Python setup
VENV_DIR = $(BASE_DIR)/.venv
PYPROJECT_TOML = $(RENDERER_DIR)/pyproject.toml

# Node setup
NODE_MODULES_DIR = $(WEBSITE_DIR)/node_modules
PNPM_LOCK_FILE = $(WEBSITE_DIR)/pnpm-lock.yaml
PACKAGE_JSON = $(WEBSITE_DIR)/package.json

# Source files
CV_DATA = $(BASE_DIR)/cv_data.yaml

# PDF dependencies
OUT_PDF = $(TEX_DIR)/cv.pdf
OUT_TEX = $(TEX_DIR)/cv.tex

# Website dependencies
OUT_HTML = $(WEBSITE_DIR)/index.html
OUT_SITEMAP = $(WEBSITE_DIR)/public/sitemap.xml
OUT_JS = $(WEBSITE_DIR)/src/template_params.js
OUT_WEBMANIFEST = $(WEBSITE_DIR)/public/img/favicon/site.webmanifest
WEBSITE_PDF = $(WEBSITE_DIR)/public/cv.pdf
WEBSITE_DIST = $(WEBSITE_DIR)/dist
WEBSITE_DEPS = $(OUT_HTML) $(OUT_SITEMAP) $(WEBSITE_PDF) $(OUT_JS) $(OUT_WEBMANIFEST)

# Input templates
INPUT_TEMPLATE_tex = $(TEMPLATES_DIR)/tex/cv-deedy.tex.j2
INPUT_TEMPLATE_html = $(TEMPLATES_DIR)/web/index.html.j2
INPUT_TEMPLATE_sitemap = $(TEMPLATES_DIR)/web/sitemap.xml.j2
INPUT_TEMPLATE_js = $(TEMPLATES_DIR)/web/template_params.js.j2
INPUT_TEMPLATE_webmanifest = $(TEMPLATES_DIR)/web/site.webmanifest.json.j2

# Output rendered templates
OUTPUT_RENDERED_tex = $(OUT_TEX)
OUTPUT_RENDERED_html = $(OUT_HTML)
OUTPUT_RENDERED_sitemap = $(OUT_SITEMAP)
OUTPUT_RENDERED_js = $(OUT_JS)
OUTPUT_RENDERED_webmanifest = $(OUT_WEBMANIFEST)

# Dependencies
CV_CLS = $(TEX_DIR)/deedy-resume.cls

# Render targets
RENDER_TARGETS = tex html sitemap js webmanifest
RENDER_OUTPUTS = $(foreach _target,$(RENDER_TARGETS),$(OUTPUT_RENDERED_$(_target)))

# CI downloads
WEBSITE_BUNDLE_ARCHIVE = $(DOWNLOADS_DIR)/gh-pages-bundle.tar.gz

# Marker files
WEBSITE_BUILD_MARKER = $(BUILD_DIR)/.build-website.stamp
WEBSITE_BUILD_FROM_BUNDLE_MARKER = $(BUILD_DIR)/.build-website-from-bundle.stamp
RELEASE_BUILD_MARKER = $(BUILD_DIR)/.build-release.stamp
MODULES_MARKER = $(NODE_MODULES_DIR)/.install-deps-node.stamp
MODULES_FROZEN_MARKER = $(NODE_MODULES_DIR)/.install-deps-node-frozen.stamp
VENV_MARKER = $(VENV_DIR)/.setup-env-python.stamp
PYTHON_DEPS_MARKER = $(VENV_DIR)/.install-deps-python.stamp

# Commands
ACTIVATE_VENV = . $(VENV_DIR)/bin/activate
ENTER_RENDERER_DIR = $(ACTIVATE_VENV) && cd $(RENDERER_DIR)
ENTER_WEBSITE_DIR = cd $(WEBSITE_DIR)

######################################################################
#                             TARGETS                                #
######################################################################

.PHONY: all help \
        build-cv build-website build-website-from-bundle build-release \
        $(foreach _target,$(RENDER_TARGETS),render-$(_target)) \
		test-renderer \
        install-deps-node install-deps-python install-deps-node-frozen \
		preview-website-prod preview-website-dev \
        clear-cv clear-deps-node clear-deps-python clear-all \
        validate-pre-commit

.SILENT: help

all : build-cv build-website build-release

define PRINT_TARGET_HELP
	printf " - %-32s : %s\n"
endef

help :
	echo "Available targets:"
	$(PRINT_TARGET_HELP)   "all"                         "build and deploy CV locally"
	$(PRINT_TARGET_HELP)   "build-cv"                    "build CV PDF from LaTeX"
	$(PRINT_TARGET_HELP)   "build-website"               "build website"
	$(PRINT_TARGET_HELP)   "build-website-from-bundle"   "build website from release bundle"
	for _target in $(RENDER_TARGETS); do \
		$(PRINT_TARGET_HELP)   "render-$${_target}"      "generate $${_target} file from YAML data"; \
	done
	$(PRINT_TARGET_HELP)   "test-renderer"              "run tests for renderer"
	$(PRINT_TARGET_HELP)   "install-deps-node"           "install Node.js dependencies"
	$(PRINT_TARGET_HELP)   "install-deps-node-frozen"    "install Node.js dependencies (frozen)"
	$(PRINT_TARGET_HELP)   "install-deps-python"         "install Python dependencies with Poetry"
	$(PRINT_TARGET_HELP)   "preview-website-prod"        "preview website in production mode"
	$(PRINT_TARGET_HELP)   "preview-website-dev"         "preview website in development mode"
	$(PRINT_TARGET_HELP)   "clear-cv"                    "remove built CV files"
	$(PRINT_TARGET_HELP)   "clear-deps-node"             "remove Node.js dependencies"
	$(PRINT_TARGET_HELP)   "clear-deps-python"           "remove Python virtual environment and cache"
	$(PRINT_TARGET_HELP)   "clear-all"                   "remove all untracked files and directories"
	$(PRINT_TARGET_HELP)   "validate-pre-commit"         "validate pre-commit hooks"

build-cv : $(OUT_PDF)

build-website : $(WEBSITE_BUILD_MARKER)

build-website-from-bundle : $(WEBSITE_BUILD_FROM_BUNDLE_MARKER)

build-release : $(RELEASE_BUILD_MARKER)

validate-pre-commit : $(PYTHON_DEPS_MARKER) $(MODULES_MARKER)
	$(ACTIVATE_VENV) && pre-commit run --all-files

define RENDER_TARGET_RULE
render-$(1) : $(OUTPUT_RENDERED_$(1))
endef
$(foreach _target, $(RENDER_TARGETS), \
	$(eval $(call RENDER_TARGET_RULE,$(_target))))

test-renderer : $(PYTHON_DEPS_MARKER)
	$(ENTER_RENDERER_DIR) && poetry run pytest

install-deps-node : $(MODULES_MARKER)

install-deps-node-frozen : $(MODULES_FROZEN_MARKER)

install-deps-python : $(PYTHON_DEPS_MARKER)

preview-website-prod : $(WEBSITE_BUILD_MARKER)
	$(ENTER_WEBSITE_DIR) && pnpm run preview

preview-website-dev : $(WEBSITE_DEPS) $(MODULES_MARKER)
	$(ENTER_WEBSITE_DIR) && pnpm run dev

clear-cv :
	rm -f $(RENDER_OUTPUTS)
	rm -f $(WEBSITE_PDF)
	rm -rf $(WEBSITE_DIST)
	rm -rf $(BUILD_DIR)

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
	git clean -xdf

######################################################################
#                           BUILD RULES                              #
######################################################################

$(OUT_PDF) : $(OUT_TEX) $(CV_CLS)
	cd $(TEX_DIR) && latexmk -xelatex -interaction=nonstopmode -synctex=1 -file-line-error cv.tex
	touch $(OUT_PDF)

define RENDER_RULE
$(OUTPUT_RENDERED_$(1)) : $(PYTHON_DEPS_MARKER) $(CV_DATA) $(INPUT_TEMPLATE_$(1))
	$(ENTER_RENDERER_DIR) \
		&& poetry run python -m cv_renderer \
			--data $(CV_DATA) \
			--input $(INPUT_TEMPLATE_$(1)) \
			--output $(OUTPUT_RENDERED_$(1)) \
			--force
endef
$(foreach _target, $(RENDER_TARGETS), \
	$(eval $(call RENDER_RULE,$(_target))))

$(WEBSITE_PDF) : $(OUT_PDF)
	cp $(OUT_PDF) $(WEBSITE_PDF)

$(WEBSITE_BUILD_MARKER) : $(WEBSITE_DEPS) $(MODULES_MARKER) $(BUILD_DIR)
	$(ENTER_WEBSITE_DIR) && pnpm run build
	touch $(WEBSITE_BUILD_MARKER)

$(WEBSITE_BUILD_FROM_BUNDLE_MARKER) : $(WEBSITE_BUNDLE_ARCHIVE) $(MODULES_FROZEN_MARKER) $(BUILD_DIR)
	mkdir -p $(BUILD_DIR)/gh-pages-bundle
	tar -xzvf $(WEBSITE_BUNDLE_ARCHIVE) -C $(BUILD_DIR)/gh-pages-bundle
	cp -r $(BUILD_DIR)/gh-pages-bundle/* $(WEBSITE_DIR)/
	$(ENTER_WEBSITE_DIR) && pnpm run build
	touch $(WEBSITE_BUILD_FROM_BUNDLE_MARKER)

$(BUILD_DIR) :
	mkdir -p $(BUILD_DIR)

$(RELEASE_BUILD_MARKER) : $(BUILD_DIR) $(OUT_PDF) $(WEBSITE_DEPS)
	rm -rf $(RELEASE_DIR)
	mkdir -p $(RELEASE_DIR)

	cp $(OUT_PDF) $(RELEASE_DIR)/

	echo $(WEBSITE_DEPS) \
	| sed 's|$(WEBSITE_DIR)/||g' \
	| xargs tar -czvf $(RELEASE_DIR)/gh-pages-bundle.tar.gz -C $(WEBSITE_DIR)/

	touch $(RELEASE_BUILD_MARKER)

$(MODULES_MARKER) : $(PACKAGE_JSON)
	$(ENTER_WEBSITE_DIR) && pnpm install
	touch $(MODULES_MARKER)

$(MODULES_FROZEN_MARKER) : $(PACKAGE_JSON) $(PNPM_LOCK_FILE)
	$(ENTER_WEBSITE_DIR) && pnpm install --frozen-lockfile
	touch $(MODULES_FROZEN_MARKER)
	touch $(MODULES_MARKER)

$(PYTHON_DEPS_MARKER) : $(VENV_MARKER) $(PYPROJECT_TOML)
	$(ENTER_RENDERER_DIR) && poetry install
	touch $(PYTHON_DEPS_MARKER)

$(VENV_MARKER) :
	python -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install poetry
	touch $(VENV_MARKER)
