.PHONY: build

MODULE:=guake
INSTALL_ROOT:=/
PREFIX:=$(INSTALL_ROOT)usr


all: dev style checks build dists test-unit docs


dev:
	pipenv install --dev


install-local:
	pipenv install


install-system: install-schemas
	python3 setup.py install --root "$(INSTALL_ROOT)" --optimize=1


install-schemas:
	install -Dm755 "guake/data/guake.desktop" "$(PREFIX)/share/applications/guake.desktop"
	install -Dm755 "guake/data/pixmaps/guake.png" "$(PREFIX)/share/pixmaps/guake.png"


style: fiximports autopep8 yapf


fiximports:
	@for fil in $$(find setup.py install.py install-lib.py guake -name "*.py"); do \
		echo "Sorting imports from: $$fil"; \
		pipenv run fiximports $$fil; \
	done


autopep8:
	pipenv run autopep8 --in-place --recursive setup.py $(MODULE)


yapf:
	pipenv run yapf --style .yapf --recursive -i $(MODULE)


checks: update-po sdist flake8 pylint


flake8:
	pipenv run python setup.py flake8


pylint:
	pipenv run pylint --rcfile=.pylintrc --output-format=colorized $(MODULE)


build: dists


run-local:
	export GUAKE_DATA_DIR=$(shell pwd)/data ; pipenv run ./run-local.sh


shell:
	pipenv shell


test:
	pipenv run pytest $(MODULE)


test-coverage:
	pipenv run py.test -v --cov $(MODULE) --cov-report term-missing


dists: update-po sdist bdist wheels


sdist:
	pipenv run python setup.py sdist


bdist:
	pipenv run python setup.py bdist


wheels:
	pipenv run python setup.py bdist_wheel


docs:
	cd doc && make html


pypi-publish: build
	pipenv run python setup.py upload -r pypi


update:
	pipenv update
	pipenv install --dev


lock:
	pipenv lock


freeze:
	pipenv run pip freeze


githook:style


push: githook
	git push origin --tags


clean:
	pipenv --rm ; true
	find . -name "*.pyc" -exec rm -f {} \;


update-po:
	find guake -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=guake-python.pot
	find guake/data -iname "*.glade" | xargs xgettext --from-code=UTF-8  -L Glade --output=guake-glade.pot
	msgcat --use-first guake-python.pot guake-glade.pot > guake.pot
	rm guake-python.pot guake-glade.pot


# aliases to gracefully handle typos on poor dev's terminal
check: checks
devel: dev
develop: dev
dist: dists
install: install-system
pypi: pypi-publish
run: run-local
styles: style
upgrade: update
wheel: wheels
doc: docs
