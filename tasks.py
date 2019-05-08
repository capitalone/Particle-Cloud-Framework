""" Project Management Tasks """
import os
from invoke import task, Collection

namespace = Collection()

@task
def setup(ctx):
    """ Setup a virtualenv, activate it, and install requirements """
    ctx.run("virtualenv venv && source venv/bin/activate")
    ctx.run("pip install -r requirements.txt -r requirements-dev.txt")

@task
def docs_add(ctx):
    """ Run sphinx-apidoc on pcf and pcf/test """
    ctx.run("cd docs; sphinx-apidoc -o source ../pcf ../pcf/test/*")

@task
def lint(ctx):
    """ Run pylint on pcf directory """
    ctx.run("pylint pcf")

@task
def test(ctx):
    """ Run pytest on pcf directory, generating a coverage report """
    ctx.run("pytest --cov-config .coveragerc --cov=pcf --cov-report term-missing")

@task
def build(ctx, pcf_tag=None):
    """ Build PCF with the PCF_TAG value given or the VERSION in pcf/__init__.py """
    if pcf_tag:
        os.environ['PCF_TAG'] = pcf_tag
    ctx.run("python setup.py bdist_wheel")

@task(build)
def publish(ctx):
    """ Publish package to Pypi """
    ctx.run("python -m twine upload dist/*")
