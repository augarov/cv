.PHONY: all clean build deploy-local install-deps

######################################################################
#                             TARGETS                                #
######################################################################

all : build deploy-local

help :
	@echo "Available targets:"
	@echo " - all            : build and deploy locally"
	@echo " - build          : build cv.pdf"
	@echo " - deploy-local   : deploy cv.pdf to gh-pages"
	@echo " - install-deps   : install dependencies"

build : cv.pdf

deploy-local : gh-pages/cv.pdf

install-deps : gh-pages/node_modules/.modules.yaml

clean :
	rm -f cv.pdf
	rm -f gh-pages/cv.pdf

######################################################################
#                           BUILD RULES                              #
######################################################################

cv.pdf : cv.tex deedy-resume.cls
	latexmk -xelatex -interaction=nonstopmode -synctex=1 -file-line-error cv.tex
	touch cv.pdf

gh-pages/cv.pdf : cv.pdf
	cp cv.pdf gh-pages/

gh-pages/node_modules/.modules.yaml : gh-pages/pnpm-lock.yaml
	cd gh-pages && pnpm install && touch node_modules/.modules.yaml
