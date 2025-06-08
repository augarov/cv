.PHONY: all build-cv deploy-cv install-deps-node install-deps-python install-deps-python clear-cv clear-deps-node clear-deps-python

######################################################################
#                            VARIABLES                               #
######################################################################

# Base directory
BASE_DIR = $(shell pwd)

# Directory names
TEX_DIR = $(BASE_DIR)/tex
DEPLOY_DIR = $(BASE_DIR)/gh-pages
RENDERER_DIR = $(BASE_DIR)/cv_renderer

# Python setup
VENV_DIR = $(BASE_DIR)/.venv
PYPROJECT_TOML = $(RENDERER_DIR)/pyproject.toml

# Source files
CV_TEX = $(TEX_DIR)/cv.tex
CV_CLS = $(TEX_DIR)/deedy-resume.cls

# Target files
CV_PDF = $(TEX_DIR)/cv.pdf
DEPLOY_PDF = $(DEPLOY_DIR)/cv.pdf
MODULES_MARKER = $(DEPLOY_DIR)/node_modules/.install-deps-node.stamp
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
	@echo " - deploy-cv              : deploy $(CV_PDF) to $(DEPLOY_DIR)"
	@echo " - install-deps-node      : install Node.js dependencies"
	@echo " - install-deps-python    : install Python dependencies with Poetry"
	@echo " - clear-cv               : remove built CV files"
	@echo " - clear-deps-node        : remove Node.js dependencies"
	@echo " - clear-deps-python      : remove Python virtual environment and cache"

build-cv : $(CV_PDF)

deploy-cv : $(DEPLOY_PDF)

install-deps-node : $(MODULES_MARKER)

install-deps-python : $(PYTHON_DEPS_MARKER)

clear-cv :
	rm -f $(CV_PDF)
	rm -f $(DEPLOY_PDF)

clear-deps-node :
	rm -rf $(DEPLOY_DIR)/node_modules
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

$(DEPLOY_PDF) : $(CV_PDF)
	cp $(CV_PDF) $(DEPLOY_DIR)/

$(MODULES_MARKER) :
	cd $(DEPLOY_DIR) && pnpm install && touch $(MODULES_MARKER)

$(PYTHON_DEPS_MARKER) : $(VENV_MARKER) $(PYPROJECT_TOML)
	. $(VENV_DIR)/bin/activate && cd $(RENDERER_DIR) && poetry install
	touch $(PYTHON_DEPS_MARKER)

$(VENV_MARKER) :
	python -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip
	. $(VENV_DIR)/bin/activate && pip install poetry
	touch $(VENV_MARKER)
