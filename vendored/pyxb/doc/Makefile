# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

EPYDOC        = epydoc
EPYDOCOPTS    = --config documentation.cfg

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d _build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html dirhtml pickle json htmlhelp qthelp latex changes linkcheck doctest
.PHONY: apihtml

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to make standalone HTML files"
	@echo "  dirhtml   to make HTML files named index.html in directories"
	@echo "  pickle    to make pickle files"
	@echo "  json      to make JSON files"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  qthelp    to make HTML files and a qthelp project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"
	@echo "  doctest   to run all doctests embedded in the documentation (if enabled)"

apihtml:
	mkdir -p html/api
	PYTHONPATH=.. $(EPYDOC) $(EPYDOCOPTS)

pyxbgen_cli.txt: ../pyxb/binding/generate.py ../maintainer/gendoc
	PYTHONPATH=.. ../maintainer/gendoc \
        | sed -e 's@  *$$@@' \
        > $@

GENERATED_TXT += pyxbgen_cli.txt

html: $(GENERATED_TXT)
	PYTHONPATH=. $(SPHINXBUILD) -b html $(ALLSPHINXOPTS) html
	@echo
	@echo "Build finished. The HTML pages are in _build/html."

clean:
	-rm -rf html _build ${GENERATED_TXT}
