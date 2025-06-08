.PHONY: all clean build deploy-local install-deps

######################################################################
#                            VARIABLES                               #
######################################################################

# Directory names
TEX_DIR = tex
DEPLOY_DIR = gh-pages

# Source files
CV_TEX = $(TEX_DIR)/cv.tex
CV_CLS = $(TEX_DIR)/deedy-resume.cls

# Target files
CV_PDF = $(TEX_DIR)/cv.pdf
DEPLOY_PDF = $(DEPLOY_DIR)/cv.pdf
MODULES_MARKER = $(DEPLOY_DIR)/node_modules/.modules.yaml
PNPM_LOCK = $(DEPLOY_DIR)/pnpm-lock.yaml

######################################################################
#                             TARGETS                                #
######################################################################

all : build deploy-local

help :
	@echo "Available targets:"
	@echo " - all            : build and deploy locally"
	@echo " - build          : build $(CV_PDF)"
	@echo " - deploy-local   : deploy $(CV_PDF) to $(DEPLOY_DIR)"
	@echo " - install-deps   : install dependencies"

build : $(CV_PDF)

deploy-local : $(DEPLOY_PDF)

install-deps : $(MODULES_MARKER)

clean :
	rm -f $(CV_PDF)
	rm -f $(DEPLOY_PDF)

######################################################################
#                           BUILD RULES                              #
######################################################################

$(CV_PDF) : $(CV_TEX) $(CV_CLS)
	cd $(TEX_DIR) && latexmk -xelatex -interaction=nonstopmode -synctex=1 -file-line-error cv.tex
	touch $(CV_PDF)

$(DEPLOY_PDF) : $(CV_PDF)
	cp $(CV_PDF) $(DEPLOY_DIR)/

$(MODULES_MARKER) : $(PNPM_LOCK)
	cd $(DEPLOY_DIR) && pnpm install && touch node_modules/.modules.yaml
