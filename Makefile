# Makefile for Building the ATC-NG debian package
# ©2011 - Mac Ryan - Released under GPL v3

PACKAGED_BRANCH = master

# This directive generate the include files
pcommands.inc:
	./generate-includes.py #pcommands-include.rst

clean:
	rm -r -d *.egg-info/ dist/ distribute*.gz distribute*.egg distribute_setup.pyc deb_dist/ debian/
	find . -name ".pyc" -type d -exec rm -rf {} \;

fetch:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

deb: clean
	python setup.py --command-packages=stdeb.command bdist_deb

debianize: clean
	python setup.py --command-packages=stdeb.command debianize

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make HTML files and a qthelp project"
	@echo "  devhelp    to make HTML files and a Devhelp project"
	@echo "  epub       to make an epub"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  changes    to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"

html: pcommands.inc
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."
