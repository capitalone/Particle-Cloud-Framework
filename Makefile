.PHONY: docs

docs:
	cd docs; make html

docs-add:
	cd docs; sphinx-apidoc -o source ../pcf ../pcf/test/*

build:
	export PCF_TAG=$(PCF_TAG)
	python setup.py bdist_wheel

publish:
	python -m twine upload dist/*

lint:
	pylint pcf

test:
	pytest --cov-config .coveragerc --cov=pcf --cov-report term-missing
