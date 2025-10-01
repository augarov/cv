.PHONY: all \
        build-cv build-website build-website-from-bundle build-release \
        render-tex render-html \
        install-deps-node install-deps-python install-deps-node-frozen \
        clear-cv clear-deps-node clear-deps-python \
        validate-pre-commit

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

# Source files
CV_DATA = $(BASE_DIR)/cv_data.yaml
OUT_TEX_TEMPLATE = $(TEMPLATES_DIR)/cv.tex.j2
OUT_HTML_TEMPLATE = $(TEMPLATES_DIR)/cv.html.j2
OUT_TEX = $(TEX_DIR)/cv.tex
CV_CLS = $(TEX_DIR)/deedy-resume.cls

# Target files
OUT_PDF = $(TEX_DIR)/cv.pdf
OUT_HTML = $(WEBSITE_DIR)/index.html
DEPLOY_PDF = $(WEBSITE_DIR)/public/cv.pdf
WEBSITE_DIST = $(WEBSITE_DIR)/dist

# CI downloads
WEBSITE_BUNDLE_ARCHIVE = $(DOWNLOADS_DIR)/gh-pages-bundle.tar.gz

# Marker files
WEBSITE_BUILD_MARKER = $(BUILD_DIR)/.build-website.stamp
WEBSITE_BUILD_FROM_BUNDLE_MARKER = $(BUILD_DIR)/.build-website-from-bundle.stamp
RELEASE_BUILD_MARKER = $(BUILD_DIR)/.build-release.stamp
MODULES_MARKER = $(WEBSITE_DIR)/node_modules/.install-deps-node.stamp
MODULES_FROZEN_MARKER = $(WEBSITE_DIR)/node_modules/.install-deps-node-frozen.stamp
VENV_MARKER = $(VENV_DIR)/.setup-env-python.stamp
PYTHON_DEPS_MARKER = $(VENV_DIR)/.install-deps-python.stamp

# Commands
ACTIVATE_VENV = . $(VENV_DIR)/bin/activate

######################################################################
#                             TARGETS                                #
######################################################################

all : build-cv build-website build-release

help :
	@echo "Available targets:"
	@echo " - all                         : build and deploy CV locally"
	@echo " - build-cv                    : build CV PDF from LaTeX"
	@echo " - build-website               : build website"
	@echo " - build-website-from-bundle   : build website from release bundle"
	@echo " - build-release               : build release bundle"
	@echo " - render-tex                  : generate LaTeX file from YAML data"
	@echo " - render-html                 : generate HTML file from YAML data"
	@echo " - install-deps-node           : install Node.js dependencies"
	@echo " - install-deps-node-frozen    : install Node.js dependencies (frozen)"
	@echo " - install-deps-python         : install Python dependencies with Poetry"
	@echo " - clear-cv                    : remove built CV files"
	@echo " - clear-deps-node             : remove Node.js dependencies"
	@echo " - clear-deps-python           : remove Python virtual environment and cache"
	@echo " - validate-pre-commit         : validate pre-commit hooks"

build-cv : $(OUT_PDF)

build-website : $(WEBSITE_BUILD_MARKER)

build-website-from-bundle : $(WEBSITE_BUILD_FROM_BUNDLE_MARKER)

build-release : $(RELEASE_BUILD_MARKER)

validate-pre-commit : $(PYTHON_DEPS_MARKER) $(MODULES_MARKER)
	$(ACTIVATE_VENV) && pre-commit run --all-files

render-tex : $(OUT_TEX)

render-html : $(OUT_HTML)

install-deps-node : $(MODULES_MARKER)

install-deps-node-frozen : $(MODULES_FROZEN_MARKER)

install-deps-python : $(PYTHON_DEPS_MARKER)

clear-cv :
	rm -f $(OUT_TEX)
	rm -f $(OUT_HTML)
	rm -f $(OUT_PDF)
	rm -f $(DEPLOY_PDF)
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

######################################################################
#                           BUILD RULES                              #
######################################################################

$(OUT_PDF) : $(OUT_TEX) $(CV_CLS)
	cd $(TEX_DIR) && latexmk -xelatex -interaction=nonstopmode -synctex=1 -file-line-error cv.tex
	touch $(OUT_PDF)

$(OUT_TEX) : $(PYTHON_DEPS_MARKER) $(CV_DATA) $(OUT_TEX_TEMPLATE)
	$(ACTIVATE_VENV) && python -m cv_renderer --output $(OUT_TEX) --template $(OUT_TEX_TEMPLATE) --data $(CV_DATA)

$(OUT_HTML) : $(PYTHON_DEPS_MARKER) $(CV_DATA) $(OUT_HTML_TEMPLATE)
	$(ACTIVATE_VENV) && python -m cv_renderer --output $(OUT_HTML) --template $(OUT_HTML_TEMPLATE) --data $(CV_DATA)

$(DEPLOY_PDF) : $(OUT_PDF)
	cp $(OUT_PDF) $(DEPLOY_PDF)

$(WEBSITE_BUILD_MARKER) : $(OUT_HTML) $(DEPLOY_PDF) $(MODULES_MARKER) $(BUILD_DIR)
	cd $(WEBSITE_DIR) && pnpm run build
	touch $(WEBSITE_BUILD_MARKER)

$(WEBSITE_BUILD_FROM_BUNDLE_MARKER) : $(WEBSITE_BUNDLE_ARCHIVE) $(MODULES_FROZEN_MARKER) $(BUILD_DIR)
	mkdir -p $(BUILD_DIR)/gh-pages-bundle
	tar -xzvf $(WEBSITE_BUNDLE_ARCHIVE) -C $(BUILD_DIR)/gh-pages-bundle
	cp -r $(BUILD_DIR)/gh-pages-bundle/* $(WEBSITE_DIR)/
	cd $(WEBSITE_DIR) && pnpm run build
	touch $(WEBSITE_BUILD_FROM_BUNDLE_MARKER)

$(BUILD_DIR) :
	mkdir -p $(BUILD_DIR)

$(RELEASE_BUILD_MARKER) : $(BUILD_DIR) $(OUT_PDF) $(OUT_HTML)
	mkdir -p $(WEBSITE_BUNDLE_DIR)
	cp $(OUT_HTML) $(WEBSITE_BUNDLE_DIR)/

	mkdir -p $(WEBSITE_BUNDLE_DIR)/public
	cp $(OUT_PDF) $(WEBSITE_BUNDLE_DIR)/public/

	mkdir -p $(RELEASE_DIR)
	cp $(OUT_PDF) $(RELEASE_DIR)/
	tar -czvf $(RELEASE_DIR)/gh-pages-bundle.tar.gz -C $(WEBSITE_BUNDLE_DIR)/ .

	touch $(RELEASE_BUILD_MARKER)

$(MODULES_MARKER) :
	cd $(WEBSITE_DIR) && pnpm install
	touch $(MODULES_MARKER)

$(MODULES_FROZEN_MARKER) :
	cd $(WEBSITE_DIR) && pnpm install --frozen-lockfile
	touch $(MODULES_FROZEN_MARKER)
	touch $(MODULES_MARKER)

$(PYTHON_DEPS_MARKER) : $(VENV_MARKER) $(PYPROJECT_TOML)
	$(ACTIVATE_VENV) && cd $(RENDERER_DIR) && poetry install
	touch $(PYTHON_DEPS_MARKER)

$(VENV_MARKER) :
	python -m venv $(VENV_DIR)
	$(ACTIVATE_VENV) && pip install --upgrade pip
	$(ACTIVATE_VENV) && pip install poetry
	touch $(VENV_MARKER)
