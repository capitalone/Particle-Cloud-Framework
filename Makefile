.PHONY: docs

# Makefile is not used in CICD. Kept around for legacy compatibility
# See tasks.py to edit the CICD pipeline

docs:
	cd docs; make html

docs-add:
	cd docs; sphinx-apidoc -o source ../pcf ../pcf/test/*

pypi-build:
	export PCF_TAG=$(PCF_TAG)
	python setup.py bdist_wheel
	python -m twine upload dist/*

test:
	pytest --cov-config .coveragerc --cov=pcf --cov-report term-missing
