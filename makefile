SHELL = /usr/bin/env bash

_python ?= python
PYTESTPARALLEL ?= --workers auto
COVHTML ?= --cov-report html
# for bump2version, valid options are: major, minor, patch
PART ?= patch
N_MPI ?= 4

_pandoc = pandoc
pandocArgs = --toc -M date="`date "+%B %e, %Y"`" --filter=pantable --wrap=none
RSTs = CHANGELOG.rst README.rst

# Main Targets #################################################################

.PHONY: test test-mpi docs clean env_variant_generator

docs: $(RSTs)
	$(MAKE) html
html: dist/docs/
env_variant_generator:
	for os in windows linux macos; do \
		$(_python) -m pmpm.env_variant_generator examples/$$os.yml --mkl -o examples/$$os-mkl.yml; \
		$(_python) -m pmpm.env_variant_generator examples/$$os.yml --no-mkl -o examples/$$os-nomkl.yml; \
	done

test:
	$(_python) -m pytest -vv $(PYTESTPARALLEL) \
		--cov=src --cov-report term $(COVHTML) --no-cov-on-fail --cov-branch \
		tests

test-mpi:
	mpirun -n $(N_MPI) $(_python) -m pytest -vv --with-mpi \
		--capture=no \
		tests

clean:
	rm -f $(RSTs)

# docs #########################################################################

README.rst: docs/README.md docs/badges.csv
	printf \
		"%s\n\n" \
		".. This is auto-generated from \`$<\`. Do not edit this file directly." \
		> $@
	cd $(<D); \
	$(_pandoc) $(pandocArgs) $(<F) -V title='pantable Documentation' -s -t rst \
		>> ../$@

%.rst: %.md
	printf \
		"%s\n\n" \
		".. This is auto-generated from \`$<\`. Do not edit this file directly." \
		> $@
	$(_pandoc) $(pandocArgs) $< -s -t rst >> $@

dist/docs/:
	mkdir -p $@
	sphinx-build -E -b dirhtml docs $@
    # sphinx-build -b linkcheck docs dist/docs

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

gh-pages:
	ghp-import --no-jekyll --push dist/docs

# check python styles
pep8:
	pycodestyle . --ignore=E501
flake8:
	flake8 . --ignore=E501
pylint:
	pylint pmpm

print-%:
	$(info $* = $($*))

# poetry #######################################################################

setup.py:
	poetry build
	cd dist; tar -xf pmpm-0.1.0.tar.gz pmpm-0.1.0/setup.py
	mv dist/pmpm-0.1.0/setup.py .
	rm -rf dist/pmpm-0.1.0

# since poetry doesn't support editable, we can build and extract the setup.py,
# temporary remove pyproject.toml and ask pip to install from setup.py instead.
editable: setup.py
	mv pyproject.toml .pyproject.toml
	$(_python) -m pip install --no-dependencies -e .
	mv .pyproject.toml pyproject.toml

# releasing ####################################################################

bump:
	bump2version $(PART)
	git push --follow-tags
