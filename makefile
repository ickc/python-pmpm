SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = docs
BUILDDIR      = dist/docs

# for bump-my-version, valid options are: major, minor, patch
PART ?= patch

PORT ?= 8099
DOC_DEP = $(shell find docs -type f \( -name '*.md' -o -name '*.rst' \)) $(shell find src -type f -name '*.py')

# documentation ################################################################

.PHONY: all doc epub
all: doc epub pdf man txt html
doc: $(BUILDDIR)/dirhtml/.sentinel
epub: $(BUILDDIR)/epub/pmpm.epub
pdf: $(BUILDDIR)/latexpdf/latex/pmpm.pdf
man: $(BUILDDIR)/man/pmpm.1
txt: $(BUILDDIR)/singlehtml/pmpm.txt
html: $(BUILDDIR)/singlehtml/index.html

$(BUILDDIR)/dirhtml/.sentinel: $(DOC_DEP)
	@$(SPHINXBUILD) -b dirhtml "$(SOURCEDIR)" "$(BUILDDIR)/dirhtml" $(SPHINXOPTS)
	touch $@
$(BUILDDIR)/epub/pmpm.epub: $(DOC_DEP)
	@$(SPHINXBUILD) -b epub "$(SOURCEDIR)" "$(BUILDDIR)/epub" $(SPHINXOPTS)
$(BUILDDIR)/latexpdf/latex/pmpm.pdf: $(DOC_DEP)
	@$(SPHINXBUILD) -M latexpdf "$(SOURCEDIR)" "$(BUILDDIR)/latexpdf" $(SPHINXOPTS)
$(BUILDDIR)/man/pmpm.1: $(DOC_DEP)
	@$(SPHINXBUILD) -b man "$(SOURCEDIR)" "$(BUILDDIR)/man" $(SPHINXOPTS)
$(BUILDDIR)/singlehtml/index.html: $(DOC_DEP)
	@$(SPHINXBUILD) -b singlehtml "$(SOURCEDIR)" "$(BUILDDIR)/singlehtml" $(SPHINXOPTS)
$(BUILDDIR)/singlehtml/pmpm.txt: $(BUILDDIR)/singlehtml/index.html
	pandoc -f html -t plain $< -o $@

.PHONY: serve
serve: doc
	sphinx-autobuild \
		-b dirhtml $(SPHINXOPTS) \
		--port $(PORT) \
		--open-browser \
		--delay 0 \
		"$(SOURCEDIR)" "$(BUILDDIR)"

# env_variant_generator ########################################################

.PHONY: env_variant_generator clean

env_variant_generator:
	for os in linux macos; do \
		for mpi in nompi openmpi mpich; do \
			python -m pmpm.env_variant_generator examples/$$os.yml --mpi $$mpi --os $$os --mkl --output examples/$$os-mkl-$$mpi.yml; \
			python -m pmpm.env_variant_generator examples/$$os.yml --mpi $$mpi --os $$os --no-mkl --output examples/$$os-nomkl-$$mpi.yml; \
		done \
	done

clean:
	rm -f examples/linux-*.yml examples/macos-*.yml
	rm -rf dist

# maintenance ##################################################################

.PHONY: pypi pypiManual gh-pages pep8 flake8 pylint
# Deploy to PyPI
## by CI, properly git tagged
pypi:
	git push origin v0.1.0
## Manually
pypiManual:
	rm -rf dist
	# tox -e check
	poetry build
	twine upload dist/*

# releasing ####################################################################

bump:
	bump-my-version bump $(PART)
	git push --follow-tags

print-%:
	$(info $* = $($*))
