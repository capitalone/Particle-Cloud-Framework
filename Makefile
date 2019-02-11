.PHONY: docs

docs:
	cd docs; make html

docs-add:
	cd docs; sphinx-apidoc -o source ../pcf ../pcf/test/*

pypi-build:
	export PCF_TAG=$(PCF_TAG)
	python setup.py bdist_wheel
	python -m twine upload dist/*

