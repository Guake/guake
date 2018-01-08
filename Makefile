.PHONY: build dev

MODULE:=guake
INSTALL_ROOT:=/
PREFIX:=$(INSTALL_ROOT)usr
SLUG:=fragment_name


all: dev style checks dists test docs


dev: pipenv-install-dev requirements ln-venv setup-githook

dev-no-pipenv: clean
	virtualenv --python python3 .venv
	. .venv/bin/activate && pip3 install -r requirements.txt -r requirements-dev.txt -e .

pipenv-install-dev:
	pipenv install --dev
	# vext.gi does not install on my system if using from binary (PTH error)
	pipenv run pip uninstall -y vext.gi
	pipenv run pip install -i https://pypi.python.org/pypi/ vext.gi --no-binary ':all:'

ln-venv:
	# use that to configure a symbolic link to the virtualenv in .venv
	rm -rf .venv
	ln -s $$(pipenv --venv) .venv

install-system: install-schemas install-locale
	@echo "Installing from on your system is not recommended."
	@echo "Please prefer you application package manager (apt, yum, ...)"
	@pip3 install -r requirements.txt
	@python3 setup.py install --root "$(INSTALL_ROOT)" --optimize=1

install-locale: generate-mo
	for f in $$(find po -iname "*.mo"); do \
		l="$${f%%.*}"; \
		lb=$$(basename $$l); \
		install -Dm755 "$$f" "$(PREFIX)/share/locale/$$lb/LC_MESSAGES/guake.mo"; \
	done;

install-schemas: generate-desktop
	install -Dm755 "guake/data/guake.desktop" "$(PREFIX)/share/applications/guake.desktop"
	install -Dm755 "guake/data/guake-prefs.desktop" "$(PREFIX)/share/applications/guake-prefs.desktop"
	install -Dm755 "guake/data/pixmaps/guake.png" "$(PREFIX)/share/pixmaps/guake.png"


style: fiximports autopep8 yapf


fiximports:
	@for fil in $$(find setup.py guake -name "*.py"); do \
		echo "Sorting imports from: $$fil"; \
		pipenv run fiximports $$fil; \
	done

autopep8:
	pipenv run autopep8 --in-place --recursive setup.py $(MODULE)

yapf:
	pipenv run yapf --style .yapf --recursive -i $(MODULE)


checks: update-po requirements flake8 pylint

flake8:
	pipenv run python setup.py flake8

pylint:
	pipenv run pylint --rcfile=.pylintrc --output-format=colorized $(MODULE)


dists: update-po requirements rm-dists sdist bdist wheels
build: dists

sdist:
	pipenv run python setup.py sdist

rm-dists:
	rm -rf build dist

bdist:
	pipenv run python setup.py bdist

wheels:
	pipenv run python setup.py bdist_wheel


run-local:
	GUAKE_DATA_DIR=$(shell pwd)/data PYTHONPATH=$(shell pwd) pipenv run python3 guake/main.py --no-startup-script


shell:
	pipenv shell


test:
	pipenv run pytest $(MODULE)

test-coverage:
	pipenv run py.test -v --cov $(MODULE) --cov-report term-missing


docs:
	cd doc && pipenv run make html


pypi-publish: build
	pipenv run python setup.py upload -r pypi


update:
	pipenv update
	pipenv install --dev


lock: pipenv-lock requirements

requirements:
	pipenv run pipenv_to_requirements -f

pipenv-lock:
	pipenv lock


freeze:
	pipenv run pip freeze


githook:
	bash git-hooks/post-commit

setup-githook:
	cp -fv git-hooks/* .git/hooks/


push: githook
	git push origin --tags


clean: rm-dists
	@pipenv --rm ; true
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -rf .venv .eggs *.egg-info po/*.pot
	@echo "clean successful"


update-po:
	find guake -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=guake-python.pot
	find guake/data -iname "*.glade" | xargs xgettext --from-code=UTF-8  -L Glade --output=guake-glade.pot
	(find guake/data -iname "*.desktop" | xargs xgettext --from-code=UTF-8  -L Desktop --output=guake-desktop.pot) || (echo "Skipping .desktop files, is your gettext version < 0.19.1?" && touch guake-desktop.pot)
	msgcat --use-first guake-python.pot guake-glade.pot guake-desktop.pot > po/guake.pot
	rm guake-python.pot guake-glade.pot guake-desktop.pot
	for f in $$(find po -iname "*.po"); do \
		msgcat --use-first "$$f" po/guake.pot > "$$f.new"; \
		mv "$$f.new" $$f; \
	done;

pot: update-po

generate-mo:
	for f in $$(find po -iname "*.po"); do \
		l="$${f%%.*}"; \
		msgfmt "$$f" -o "$$l.mo"; \
	done;


generate-desktop:
	msgfmt --desktop --template=guake/data/guake.template.desktop -d po -o guake/data/guake.desktop || (echo "Skipping .desktop files, is your gettext version < 0.19.1?" && cp guake/data/guake.template.desktop guake/data/guake.desktop)
	msgfmt --desktop --template=guake/data/guake-prefs.template.desktop -d po -o guake/data/guake-prefs.desktop || (echo "Skipping .desktop files, is your gettext version < 0.19.1?" && cp guake/data/guake-prefs.template.desktop guake/data/guake-prefs.desktop)


reno:
	pipenv run reno new $(SLUG)

reno-lint:
	pipenv run reno lint

release-note: reno-lint release-note-news release-note-github

release-note-news:
	@echo "Generating release note for NEWS file"
	@pipenv run reno report 2>/dev/null | \
		pandoc -f rst -t asciidoc --normalize --wrap=none --columns=100 --atx-headers | \
		grep -v '\[\[' | \
		grep -v -E '^\.\.' > NEWS.tmp
	@echo >> NEWS.tmp
	@echo >> NEWS.tmp
	@cat NEWS >> NEWS.tmp
	@rm -f NEWS
	@mv NEWS.tmp NEWS

release-note-github:
	@echo
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "!! Generating release note for GitHub !!"
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "-------- copy / paste from here --------"
	@# markdown_github to be avoided => gfm output comes in pandoc 2.0.4 release dec 2017
	@pipenv run reno report 2>/dev/null | \
		pandoc -f rst -t markdown --atx-headers --columns=100 --wrap=auto --tab-stop 2 | \
		tr '\n' '\r' | \
			sed 's/\r<!-- -->\r\r//g' | \
		tr '\r' '\n'


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
