.PHONY: docs

docs:
	cd docs; make html

docs-add:
	cd docs; sphinx-apidoc -o source ../pcf ../pcf/test/*
