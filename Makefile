.PHONY: all build-cv deploy-cv render-tex render-html install-deps-node install-deps-python clear-cv clear-deps-node clear-deps-python

######################################################################
#                            VARIABLES                               #
######################################################################

# Base directory
BASE_DIR = $(shell pwd)

# Directory names
TEX_DIR = $(BASE_DIR)/tex
WEBSITE_DIR = $(BASE_DIR)/gh-pages
RENDERER_DIR = $(BASE_DIR)/cv_renderer

# Python setup
VENV_DIR = $(BASE_DIR)/.venv
PYPROJECT_TOML = $(RENDERER_DIR)/pyproject.toml

# Source files
CV_DATA = $(BASE_DIR)/cv_data.yaml
CV_TEX_TEMPLATE = $(BASE_DIR)/templates/cv.tex.j2
CV_HTML_TEMPLATE = $(BASE_DIR)/templates/cv.html.j2
CV_TEX = $(TEX_DIR)/cv.tex
CV_CLS = $(TEX_DIR)/deedy-resume.cls

# Target files
CV_PDF = $(TEX_DIR)/cv.pdf
CV_HTML = $(WEBSITE_DIR)/cv.html
DEPLOY_PDF = $(WEBSITE_DIR)/cv.pdf
MODULES_MARKER = $(WEBSITE_DIR)/node_modules/.install-deps-node.stamp
VENV_MARKER = $(VENV_DIR)/.setup-env-python.stamp
PYTHON_DEPS_MARKER = $(VENV_DIR)/.install-deps-python.stamp

######################################################################
#                             TARGETS                                #
######################################################################

all : build-cv deploy-cv

help :
	@echo "Available targets:"
	@echo " - all                    : build and deploy CV locally"
	@echo " - build-cv               : build $(CV_PDF)"
	@echo " - deploy-cv              : deploy $(CV_PDF) to $(WEBSITE_DIR)"
	@echo " - render-tex             : generate $(CV_TEX) from YAML data"
	@echo " - render-html            : generate $(CV_HTML) from YAML data"
	@echo " - install-deps-node      : install Node.js dependencies"
	@echo " - install-deps-python    : install Python dependencies with Poetry"
	@echo " - clear-cv               : remove built CV files"
	@echo " - clear-deps-node        : remove Node.js dependencies"
	@echo " - clear-deps-python      : remove Python virtual environment and cache"

build-cv : $(CV_PDF)

deploy-cv : $(DEPLOY_PDF)

render-tex : $(CV_TEX)

render-html : $(CV_HTML)

install-deps-node : $(MODULES_MARKER)

install-deps-python : $(PYTHON_DEPS_MARKER)

clear-cv :
	rm -f $(CV_TEX)
	rm -f $(CV_HTML)
	rm -f $(CV_PDF)
	rm -f $(DEPLOY_PDF)

clear-deps-node :
	rm -rf $(WEBSITE_DIR)/node_modules
	rm -f $(MODULES_MARKER)

clear-deps-python :
	rm -rf $(VENV_DIR)
	rm -f $(PYTHON_DEPS_MARKER)
	rm -rf __pycache__
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

######################################################################
#                           BUILD RULES                              #
######################################################################

$(CV_PDF) : $(CV_TEX) $(CV_CLS)
	cd $(TEX_DIR) && latexmk -xelatex -interaction=nonstopmode -synctex=1 -file-line-error cv.tex
	touch $(CV_PDF)

$(CV_TEX) : $(PYTHON_DEPS_MARKER) $(CV_DATA) $(CV_TEX_TEMPLATE)
	. $(VENV_DIR)/bin/activate && python -m cv_renderer --format latex --output $(CV_TEX)

$(CV_HTML) : $(PYTHON_DEPS_MARKER) $(CV_DATA) $(CV_HTML_TEMPLATE)
	. $(VENV_DIR)/bin/activate && python -m cv_renderer --format html --output $(CV_HTML)

$(DEPLOY_PDF) : $(CV_PDF)
	cp $(CV_PDF) $(WEBSITE_DIR)/

$(MODULES_MARKER) :
	cd $(WEBSITE_DIR) && pnpm install && touch $(MODULES_MARKER)

$(PYTHON_DEPS_MARKER) : $(VENV_MARKER) $(PYPROJECT_TOML)
	. $(VENV_DIR)/bin/activate && cd $(RENDERER_DIR) && poetry install
	touch $(PYTHON_DEPS_MARKER)

$(VENV_MARKER) :
	python -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip
	. $(VENV_DIR)/bin/activate && pip install poetry
	touch $(VENV_MARKER)
