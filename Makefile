.PHONY: build

MODULE:=guake
INSTALL_ROOT:=/
PREFIX:=$(INSTALL_ROOT)usr


all: dev style checks build dists test-unit docs


dev:
	pipenv install --dev


install-local:
	pipenv install


install-system: install-schemas install-locale
	python3 setup.py install --root "$(INSTALL_ROOT)" --optimize=1

install-locale: generate-mo
	for f in $$(find po -iname "*.mo"); do \
		l="$${f%%.*}"; \
		lb=$$(basename $$l); \
		install -Dm755 "$$f" "$(PREFIX)/share/locale/$$lb/LC_MESSAGES/guake.mo"; \
	done;

install-schemas:
	install -Dm755 "guake/data/guake.desktop" "$(PREFIX)/share/applications/guake.desktop"
	install -Dm755 "guake/data/guake-prefs.desktop" "$(PREFIX)/share/applications/guake-prefs.desktop"
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
	find guake/data -iname "*.desktop" | xargs xgettext --from-code=UTF-8  -L Desktop --output=guake-desktop.pot
	msgcat --use-first guake-python.pot guake-glade.pot guake-desktop.pot > po/guake.pot
	rm guake-python.pot guake-glade.pot guake-desktop.pot
	for f in $$(find po -iname "*.po"); do \
		msgcat --use-first "$$f" po/guake.pot > "$$f.new"; \
		mv "$$f.new" $$f; \
	done;


generate-mo:
	for f in $$(find po -iname "*.po"); do \
		l="$${f%%.*}"; \
		msgfmt "$$f" -o "$$l.mo"; \
	done;



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
