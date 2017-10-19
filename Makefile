.PHONY: build

MODULE:=guake

all: dev style checks build dists test-unit

dev:
	@pipenv install --dev

install-local:
	@pipenv install

install-system:
	@pipenv install --system

style: fiximports autopep8 yapf

fiximports:
	@for fil in $$(find . -name "*.py"); do \
		echo "Sorting imports from: $$fil"; \
		pipenv run fiximports $$fil; \
	done

autopep8:
	@pipenv run autopep8 --in-place --recursive setup.py $(MODULE)

yapf:
	@pipenv run yapf --style .yapf --recursive -i $(MODULE)

checks: sdist flake8 pylint

flake8:
	@pipenv run python setup.py flake8

pylint:
	@pipenv run pylint --rcfile=.pylintrc --output-format=colorized $(MODULE)

build: dists

run-local:
	@pipenv run $(MODULE)

shell:
	@pipenv shell

test-unit:
	@pipenv run pytest $(MODULE)

test-coverage:
	pipenv run py.test -v --cov $(MODULE) --cov-report term-missing

dists: sdist bdist wheels

sdist:
	@pipenv run python setup.py sdist

bdist:
	@pipenv run python setup.py bdist

wheels:
	@pipenv run python setup.py bdist_wheel

pypi-publish: build
	@pipenv run python setup.py upload -r pypi

update:
	@pipenv update
	@pipenv install --dev

freeze:
	@pipenv run pip freeze

githook:style

push: githook
	@git push origin --tags

# aliases to gracefully handle typos on poor dev's terminal
check: checks
devel: dev
develop: dev
dist: dists
install: install-system
pypi: pypi-publish
run: run-local
styles: style
test: test-unit
unit_test: test-unit
unit-test: test-unit
unit: test-unit
unittest: test-unit
unittests: test-unit
upgrade: update
wheel: wheels
