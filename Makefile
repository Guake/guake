.PHONY: build dev

PYTHON_INTERPRETER=python3
MODULE:=guake
INSTALL_ROOT:=/
PREFIX:=/usr/local
# findout the dist-package directory name. Under most system, users can install on dist-package.
# On debian, site-package is reserved for the official python packages and has precedence over
# dist-package
DIST_PACKAGE_NAME:=$(shell $(PYTHON_INTERPRETER) -c "import site; import os; print(os.path.basename(site.getsitepackages()[0]))")
DIST_PACKAGE=$(PREFIX)/lib/python$(shell $(PYTHON_INTERPRETER) -c "import sys; v = sys.version_info; print('{}.{}'.format(v.major, v.minor))")/$(DIST_PACKAGE_NAME)
OLD_PREFIX:=$(INSTALL_ROOT)usr
ROOT_DIR=$(shell pwd)
DATA_DIR=$(ROOT_DIR)/guake/data

AUTOSTART_FOLDER:=~/.config/autostart

DEV_IMAGE_DIR:=$(DATA_DIR)/pixmaps
DEV_LOCALE_DIR:=$(PREFIX)/share/locale
DEV_GLADE_DIR:=$(DATA_DIR)
DEV_SCHEMA_DIR:=$(DATA_DIR)

SHARE_DIR:=$(PREFIX)/share/guake
LOGIN_DESTOP_PATH = $(SHARE_DIR)
IMAGE_DIR:=$(SHARE_DIR)/pixmaps
LOCALE_DIR:=$(PREFIX)/share/locale
GLADE_DIR:=$(SHARE_DIR)
SCHEMA_DIR:=$(PREFIX)/share/glib-2.0/schemas/
SLUG:=fragment_name

default: prepare-install
	# 'make' target, so users can install guake without need to install the 'dev' dependencies

prepare-install: generate-desktop generate-paths generate-mo compile-glib-schemas-dev

reset:
	dconf reset -f /apps/guake/


all: clean dev style checks dists test docs

dev: pipenv-install-dev requirements ln-venv setup-githook prepare-install

dev-no-pipenv: clean
	virtualenv --python $(PYTHON_INTERPRETER) .venv
	. .venv/bin/activate && pip3 install -r requirements.txt -r requirements-dev.txt -e .

pipenv-install-dev:
	pipenv install --dev --python $(PYTHON_INTERPRETER); \

ln-venv:
	# use that to configure a symbolic link to the virtualenv in .venv
	rm -rf .venv
	ln -s $$(pipenv --venv) .venv

install-system: install-schemas compile-shemas install-locale
	# you probably want to execute this target with sudo:
	# sudo make install
	@echo "Installing from on your system is not recommended."
	@echo "Please prefer you application package manager (apt, yum, ...)"
	@pip3 install -r requirements.txt

	@if [ -f guake/paths.py.dev ]; then rm -f guake/paths.py.dev; fi
	@if [ -f guake/paths.py ]; then mv guake/paths.py guake/paths.py.dev; fi
	@cp -f guake/paths.py.in guake/paths.py
	@sed -i -e 's|{{ LOCALE_DIR }}|$(LOCALE_DIR)|g' guake/paths.py
	@sed -i -e 's|{{ IMAGE_DIR }}|$(IMAGE_DIR)|g' guake/paths.py
	@sed -i -e 's|{{ GLADE_DIR }}|$(GLADE_DIR)|g' guake/paths.py
	@sed -i -e 's|{{ SCHEMA_DIR }}|$(SCHEMA_DIR)|g' guake/paths.py
	@sed -i -e 's|{{ LOGIN_DESTOP_PATH }}|$(LOGIN_DESTOP_PATH)|g' guake/paths.py
	@sed -i -e 's|{{ AUTOSTART_FOLDER }}|$(AUTOSTART_FOLDER)|g' guake/paths.py

	@$(PYTHON_INTERPRETER) setup.py install --root "$(INSTALL_ROOT)" --prefix="$(PREFIX)" --optimize=1

	@rm -f guake/paths.py
	@if [ -f guake/paths.py.dev ]; then mv guake/paths.py.dev guake/paths.py; fi

	@update-desktop-database || echo "Could not run update-desktop-database, are you root?"
	@rm -rfv build *.egg-info

install-locale:
	for f in $$(find po -iname "*.mo"); do \
		l="$${f%%.*}"; \
		lb=$$(basename $$l); \
		install -Dm644 "$$f" "$(INSTALL_ROOT)$(LOCALE_DIR)/$$lb/LC_MESSAGES/guake.mo"; \
	done;

uninstall-locale: install-old-locale
	find $(LOCALE_DIR)/ -name "guake.mo" -exec rm -f {} \;

install-old-locale:
	@find $(OLD_PREFIX)/share/locale/ -name "guake.mo" -exec rm -f {} \;

install-schemas:
	install -Dm644 "guake/data/guake.desktop" "$(INSTALL_ROOT)$(PREFIX)/share/applications/guake.desktop"
	install -Dm644 "guake/data/guake-prefs.desktop" "$(INSTALL_ROOT)$(PREFIX)/share/applications/guake-prefs.desktop"
	mkdir -p $(INSTALL_ROOT)$(IMAGE_DIR)
	install -Dm644 guake/data/pixmaps/*.png "$(INSTALL_ROOT)$(IMAGE_DIR)/"
	install -Dm644 guake/data/pixmaps/*.svg "$(INSTALL_ROOT)$(IMAGE_DIR)/"
	install -Dm644 guake/data/pixmaps/guake.png "$(INSTALL_ROOT)$(PREFIX)/share/pixmaps/guake.png"
	mkdir -p $(INSTALL_ROOT)$(SHARE_DIR)
	mkdir -p $(INSTALL_ROOT)$(GLADE_DIR)
	install -Dm644  guake/data/*.glade "$(INSTALL_ROOT)$(GLADE_DIR)"
	mkdir -p $(SHARE_DIR)
	install -Dm644 "guake/data/autostart-guake.desktop" "$(INSTALL_ROOT)$(SHARE_DIR)"
	mkdir -p $(SCHEMA_DIR)
	install -Dm644 "guake/data/org.guake.gschema.xml" "$(INSTALL_ROOT)$(SCHEMA_DIR)/"

compile-shemas:
	glib-compile-schemas $(INSTALL_ROOT)$(PREFIX)/share/glib-2.0/schemas/


uninstall-system: uninstall-schemas
	@pip3 uninstall -y guake || true
	@rm -f $(INSTALL_ROOT)$(PREFIX)/bin/guake
	@rm -f $(INSTALL_ROOT)$(PREFIX)/bin/guake-prefs

purge-system: uninstall-system reset

uninstall-schemas: uninstall-old-schemas
	rm -f "$(INSTALL_ROOT)$(PREFIX)/share/applications/guake.desktop"
	rm -f "$(INSTALL_ROOT)$(PREFIX)/share/applications/guake-prefs.desktop"
	rm -fr "$(INSTALL_ROOT)$(IMAGE_DIR)"
	rm -fr "$(INSTALL_ROOT)$(SHARE_DIR)"
	rm -f "$(INSTALL_ROOT)$(SCHEMA_DIR)/org.guake.gschema.xml"

uninstall-old-schemas:
	@rm -f "$(OLD_PREFIX)/share/applications/guake.desktop"
	@rm -f "$(OLD_PREFIX)/share/applications/guake-prefs.desktop"
	@rm -f "$(OLD_PREFIX)/share/pixmaps/guake.png"
	@rm -f "$(OLD_PREFIX)/share/glib-2.0/schemas/org.guake.gschema.xml"
	@rm -f "$(OLD_PREFIX)/share/glib-2.0/schemas/schema.guake.gschema.xml"
	@rm -fr "$(OLD_PREFIX)/share/guake"
	@rm -f $(OLD_PREFIX)/lib/python$(shell $(PYTHON_INTERPRETER) -c "import sys; v = sys.version_info; print('{}.{}'.format(v.major, v.minor))")/$(DIST_PACKAGE)/guake/data/schema.guake.gschema.xml

reinstall:
	sudo make uninstall && make && sudo make install && /usr/local/bin/guake

compile-glib-schemas-dev: clean-schemas
	glib-compile-schemas --strict guake/data/

clean-schemas:
	rm -f guake/data/gschemas.compiled

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


checks: flake8 pylint reno-lint

flake8:
	pipenv run python setup.py flake8

pylint:
	pipenv run pylint --rcfile=.pylintrc --output-format=colorized $(MODULE)


sc: style check

dists: update-po requirements prepare-install rm-dists sdist bdist wheels
build: dists

sdist:
	pipenv run python setup.py sdist

rm-dists:
	rm -rf build dist

bdist:
	pipenv run python setup.py bdist

wheels:
	pipenv run python setup.py bdist_wheel


run-local: compile-glib-schemas-dev
	pipenv run ./run-local.sh

run-fr: compile-glib-schemas-dev
	LC_ALL=fr_FR.UTF8 pipenv run ./run-local.sh


shell:
	pipenv shell


test:
	pipenv run pytest $(MODULE)

test-coverage:
	pipenv run py.test -v --cov $(MODULE) --cov-report term-missing

sct: style check update-po requirements test


docs: clean-docs
	cd doc && pipenv run make html

tag-pbr:
	@{ \
		set -e ;\
		export VERSION=$$(pipenv run python setup.py --version | cut -d. -f1,2,3); \
		echo "I: Computed new version: $$VERSION"; \
		echo "I: presse ENTER to accept or type new version number:"; \
		read VERSION_OVERRIDE; \
		VERSION=$${VERSION_OVERRIDE:-$$VERSION}; \
		PROJECTNAME=$$(pipenv run python setup.py --name); \
		echo "I: Tagging $$PROJECTNAME in version $$VERSION with tag: $$VERSION" ; \
		echo "$$ git tag $$VERSION -m \"$$PROJECTNAME $$VERSION\""; \
		git tag $$VERSION -m "$$PROJECTNAME $$VERSION"; \
		echo "I: Pushing tag $$VERSION, press ENTER to continue, C-c to interrupt"; \
		read _; \
		echo "$$ git push upstream $$VERSION"; \
		git push upstream $$VERSION; \
	}
	@# Note:
	@# To sign, need gpg configured and the following command:
	@#  git tag -s $$VERSION -m \"$$PROJECTNAME $$VERSION\""

pypi-publish: build
	pipenv run python setup.py upload -r pypi


update:
	pipenv update
	pipenv install --dev


lock: pipenv-lock requirements

requirements:
	pipenv run pipenv_to_requirements

pipenv-lock:
	pipenv lock


freeze:
	pipenv run pip freeze


githook:
	bash git-hooks/post-commit

setup-githook:
	rm -f .git/hooks/post-commit
	cp -fv git-hooks/* .git/hooks/


push: githook
	git push origin --tags


clean: rm-dists clean-docs clean-po clean-schemas clean-py clean-paths
	@echo "clean successful"

clean-py:
	@pipenv --rm ; true
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -f guake/data/guake-prefs.desktop guake/data/guake.desktop
	@rm -rf .venv .eggs *.egg-info po/*.pot

clean-paths:
	rm -f guake/paths.py guake/paths.py.dev
clean-po:
	@rm -f po/guake.pot
	@find po -name "*.mo" -exec rm -f {} \;

clean-docs:
	rm -rf doc/build

update-po:
	@find guake -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=guake-python.pot
	@find guake/data -iname "*.glade" | xargs xgettext --from-code=UTF-8 \
	                                                  -L Glade \
	                                                  --output=guake-glade.pot
	@(\
	    find guake/data -iname "*.desktop" | xargs xgettext --from-code=UTF-8 \
		                                                  -L Desktop \
	                                                      --output=guake-desktop.pot \
	) || ( \
	    echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
	    touch guake-desktop.pot)
	@msgcat --use-first guake-python.pot guake-glade.pot guake-desktop.pot > po/guake.pot
	@rm guake-python.pot guake-glade.pot guake-desktop.pot
	for f in $$(find po -iname "*.po"); do \
	    echo "updating $$f"; \
	    msgcat --use-first "$$f" po/guake.pot > "$$f.new"; \
	    mv "$$f.new" $$f; \
	done;

pot: update-po

generate-mo:
	@for f in $$(find po -iname "*.po"); do \
	    echo "generating $$f"; \
		l="$${f%%.*}"; \
		msgfmt "$$f" -o "$$l.mo"; \
	done;


generate-desktop:
	@echo "generating desktop files"
	@msgfmt --desktop --template=guake/data/guake.template.desktop \
		   -d po \
		   -o guake/data/guake.desktop || ( \
			   	echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
				cp guake/data/guake.template.desktop guake/data/guake.desktop)
	@msgfmt --desktop --template=guake/data/guake-prefs.template.desktop \
		   -d po \
		   -o guake/data/guake-prefs.desktop || ( \
			   	echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
				cp guake/data/guake-prefs.template.desktop guake/data/guake-prefs.desktop)

generate-paths:
	cp -f guake/paths.py.in guake/paths.py
	# Generic
	@sed -i -e 's|{{ LOGIN_DESTOP_PATH }}||g' guake/paths.py
	@sed -i -e 's|{{ AUTOSTART_FOLDER }}||g' guake/paths.py
	# Dev environment:
	sed -i -e 's|{{ LOCALE_DIR }}|$(DEV_LOCALE_DIR)|g' guake/paths.py
	sed -i -e 's|{{ IMAGE_DIR }}|$(DEV_IMAGE_DIR)|g' guake/paths.py
	sed -i -e 's|{{ GLADE_DIR }}|$(DEV_GLADE_DIR)|g' guake/paths.py
	sed -i -e 's|{{ SCHEMA_DIR }}|$(DEV_SCHEMA_DIR)|g' guake/paths.py

reno:
	pipenv run reno new $(SLUG) --edit

reno-lint:
	pipenv run reno -q lint

release-note: reno-lint release-note-news release-note-github

release-note-news: reno-lint
	@echo "Generating release note for NEWS file"
	@rm -f guake/releasenotes/notes/reno.cache
	@pipenv run reno report --title "NEWS" 2>/dev/null | \
		pandoc -f rst -t rst  --atx-headers --columns=100 --wrap=auto --tab-stop 2 | \
		tr '\n' '\r' | \
			sed 's/\r-\ \ \r\r\ \ \ /\r-  /g' | \
			sed 's/\r\r-\ \ /\r-  /g' | \
			sed 's/~~\r-\ \ /~~\r\r-  /g' | \
		tr '\r' '\n' \
		> NEWS.rst
	@cat releasenotes/archive/NEWS.pre-3.0 >> NEWS.rst

release-note-github: reno-lint
	@echo
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "!! Generating release note for GitHub !!"
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "-------- copy / paste from here --------"
	@# markdown_github to be avoided => gfm output comes in pandoc 2.0.4 release dec 2017
	@pipenv run reno report 2>/dev/null | \
		pandoc -f rst -t markdown --atx-headers --wrap=none --tab-stop 2 | \
		tr '\n' '\r' | \
			sed 's/\r<!-- -->\r//g' | \
			sed 's/\r\-\ \r\r\ /\r-/g' | \
			sed 's/\r\ \ \:\ \ \ /\r    /g' | \
			sed 's/\r\r\ \ \ \ \-\ /\r    - /g' | \
			sed 's/\r\ \ \ \ \-\ /\r  - /g' | \
			sed 's/\r\ \ >\ \-\ /\r  - /g' | \
			sed 's/\\\#/\#/g' | \
		tr '\r' '\n'

release: dists update-po release-note

# aliases to gracefully handle typos on poor dev's terminal
check: checks
devel: dev
develop: dev
dist: dists
doc: docs
install: install-system
purge: purge-system
pypi: pypi-publish
run: run-local
styles: style
uninstall: uninstall-system
upgrade: update
wheel: wheels
