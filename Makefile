.PHONY: build dev

PYTHON?=python3
PYTHON_INTERPRETER?=$(PYTHON)
MODULE:=guake
DESTDIR:=/
PREFIX?=/usr/local
exec_prefix:=$(PREFIX)
bindir = $(exec_prefix)/bin

# Use site.getsitepackages([PREFIX]) to guess possible install paths for uninstall.
PYTHON_SITEDIRS_FOR_PREFIX="env PREFIX=$(PREFIX) $(PYTHON_INTERPRETER) scripts/all-sitedirs-in-prefix.py"
ROOT_DIR=$(shell pwd)
DATA_DIR=$(ROOT_DIR)/guake/data
COMPILE_SCHEMA:=1

datarootdir:=$(PREFIX)/share
datadir:=$(datarootdir)
localedir:=$(datarootdir)/locale
gsettingsschemadir:=$(datarootdir)/glib-2.0/schemas

AUTOSTART_FOLDER:=~/.config/autostart

DEV_DATA_DIR:=$(DATA_DIR)

SHARE_DIR:=$(datadir)/guake
GUAKE_THEME_DIR:=$(SHARE_DIR)/guake
LOGIN_DESTOP_PATH = $(SHARE_DIR)
IMAGE_DIR:=$(SHARE_DIR)/pixmaps
GLADE_DIR:=$(SHARE_DIR)
SCHEMA_DIR:=$(gsettingsschemadir)

SLUG:=fragment_name

default: prepare-install
	# 'make' target, so users can install guake without need to install the 'dev' dependencies

prepare-install: generate-desktop generate-paths generate-mo compile-glib-schemas-dev

reset:
	dconf reset -f /apps/guake/


all: clean dev style checks dists test docs

dev: clean-ln-venv ensure-pip pipenv-install-dev requirements ln-venv setup-githook \
	 prepare-install install-dev-locale
dev-actions: ensure-pip-system pipenv-install-dev requirements setup-githook prepare-install

ensure-pip:
	./scripts/bootstrap-dev-pip.sh

ensure-pip-system:
	./scripts/bootstrap-dev-pip.sh system

dev-no-pipenv: clean
	virtualenv --python $(PYTHON_INTERPRETER) .venv
	. .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt -e .

pipenv-install-dev:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv install --dev --python $(PYTHON_INTERPRETER)

ln-venv:
	# use that to configure a symbolic link to the virtualenv in .venv
	rm -rf .venv
	ln -s $$(pipenv --venv) .venv

clean-ln-venv:
	@rm -f .venv

install-system: install-schemas compile-shemas install-locale install-guake

install-guake:
	# you probably want to execute this target with sudo:
	# sudo make install
	@echo "#############################################################"
	@echo
	@echo "Installing from source on your system is not recommended."
	@echo "Please prefer you application package manager (apt, yum, ...)"
	@echo
	@echo "#############################################################"
	@if [ "$(DESTDIR)" = "" ]; then $(PYTHON_INTERPRETER) -m pip install -r requirements.txt; fi

	@rm -f guake/paths.py.dev
	@if [ -f guake/paths.py ]; then mv guake/paths.py guake/paths.py.dev; fi
	@cp -f guake/paths.py.in guake/paths.py
	@sed -i -e 's|{{ LOCALE_DIR }}|"$(localedir)"|g' guake/paths.py
	@sed -i -e 's|{{ IMAGE_DIR }}|"$(IMAGE_DIR)"|g' guake/paths.py
	@sed -i -e 's|{{ GLADE_DIR }}|"$(GLADE_DIR)"|g' guake/paths.py
	@sed -i -e 's|{{ GUAKE_THEME_DIR }}|"$(GUAKE_THEME_DIR)"|g' guake/paths.py
	@sed -i -e 's|{{ SCHEMA_DIR }}|"$(SCHEMA_DIR)"|g' guake/paths.py
	@sed -i -e 's|{{ LOGIN_DESTOP_PATH }}|"$(LOGIN_DESTOP_PATH)"|g' guake/paths.py
	@sed -i -e 's|{{ AUTOSTART_FOLDER }}|"$(AUTOSTART_FOLDER)"|g' guake/paths.py

	@$(PYTHON_INTERPRETER) setup.py install --root "$(DESTDIR)" --prefix="$(PREFIX)" --optimize=1

	@rm -f guake/paths.py
	@if [ -f guake/paths.py.dev ]; then mv guake/paths.py.dev guake/paths.py; fi

	@update-desktop-database || echo "Could not run update-desktop-database, are you root?"
	@rm -rfv build *.egg-info

install-locale:
	for f in $$(find po -iname "*.mo"); do \
		l="$${f%%.*}"; \
		lb=$$(basename $$l); \
		install -Dm644 "$$f" "$(DESTDIR)$(localedir)/$$lb/LC_MESSAGES/guake.mo"; \
	done;

install-dev-locale:
	for f in $$(find po -iname "*.mo"); do \
		l="$${f%%.*}"; \
		lb=$$(basename $$l); \
		install -Dm644 "$$f" "guake/po/$$lb/LC_MESSAGES/guake.mo"; \
	done;

uninstall-locale:
	find $(DESTDIR)$(localedir)/ -name "guake.mo" -exec rm -f "{}" + || :
	# prune two levels of empty locale/ subdirs
	find "$(DESTDIR)$(localedir)" -type d -a -empty -exec rmdir "{}" + || :
	find "$(DESTDIR)$(localedir)" -type d -a -empty -exec rmdir "{}" + || :

uninstall-dev-locale:
	@rm -rf guake/po

install-schemas:
	install -dm755                                       "$(DESTDIR)$(datadir)/applications"
	install -Dm644 "$(DEV_DATA_DIR)/guake.desktop"       "$(DESTDIR)$(datadir)/applications/"
	install -Dm644 "$(DEV_DATA_DIR)/guake-prefs.desktop" "$(DESTDIR)$(datadir)/applications/"
	install -dm755                                       "$(DESTDIR)$(datadir)/metainfo/"
	install -Dm644 "$(DEV_DATA_DIR)/guake.desktop.metainfo.xml"  "$(DESTDIR)$(datadir)/metainfo/"
	install -dm755                                 "$(DESTDIR)$(IMAGE_DIR)"
	install -Dm644 "$(DEV_DATA_DIR)"/pixmaps/*.png "$(DESTDIR)$(IMAGE_DIR)/"
	install -Dm644 "$(DEV_DATA_DIR)"/pixmaps/*.svg "$(DESTDIR)$(IMAGE_DIR)/"
	install -dm755                                     "$(DESTDIR)$(PREFIX)/share/pixmaps"
	install -Dm644 "$(DEV_DATA_DIR)/pixmaps/guake.png" "$(DESTDIR)$(PREFIX)/share/pixmaps/"
	install -dm755                                           "$(DESTDIR)$(SHARE_DIR)"
	install -Dm644 "$(DEV_DATA_DIR)/autostart-guake.desktop" "$(DESTDIR)$(SHARE_DIR)/"
	install -dm755                           "$(DESTDIR)$(GLADE_DIR)"
	install -Dm644 "$(DEV_DATA_DIR)"/*.glade "$(DESTDIR)$(GLADE_DIR)/"
	install -dm755                                         "$(DESTDIR)$(SCHEMA_DIR)"
	install -Dm644 "$(DEV_DATA_DIR)/org.guake.gschema.xml" "$(DESTDIR)$(SCHEMA_DIR)/"

compile-shemas:
	if [ $(COMPILE_SCHEMA) = 1 ]; then glib-compile-schemas $(DESTDIR)$(gsettingsschemadir); fi

uninstall-system: uninstall-schemas uninstall-locale
	$(SHELL) -c $(PYTHON_SITEDIRS_FOR_PREFIX) \
		| while read sitedir; do \
			echo "rm -rf $(DESTDIR)$$sitedir/{guake,guake-*.egg-info}"; \
			rm -rf $(DESTDIR)$$sitedir/guake; \
			rm -rf $(DESTDIR)$$sitedir/guake-*.egg-info; \
		done
	rm -f "$(DESTDIR)$(bindir)/guake"
	rm -f "$(DESTDIR)$(bindir)/guake-prefs"
	rm -f "$(DESTDIR)$(bindir)/guake-toggle"

purge-system: uninstall-system reset

uninstall-schemas:
	rm -f "$(DESTDIR)$(datadir)/applications/guake.desktop"
	rm -f "$(DESTDIR)$(datadir)/applications/guake-prefs.desktop"
	rm -f "$(DESTDIR)$(datadir)/metainfo/guake.desktop.metainfo.xml"
	rm -f "$(DESTDIR)$(datadir)/pixmaps/guake.png"
	rm -fr "$(DESTDIR)$(IMAGE_DIR)"
	rm -fr "$(DESTDIR)$(SHARE_DIR)"
	rm -f "$(DESTDIR)$(SCHEMA_DIR)/org.guake.gschema.xml"
	rm -f "$(DESTDIR)$(SCHEMA_DIR)/gschemas.compiled"

reinstall:
	sudo make uninstall && make && sudo make install && $(DESTDIR)$(bindir)/guake

reinstall-v:
	sudo make uninstall && make && sudo make install && $(DESTDIR)$(bindir)/guake -v

compile-glib-schemas-dev: clean-schemas
	glib-compile-schemas --strict $(DEV_DATA_DIR)

clean-schemas:
	rm -f $(DEV_DATA_DIR)/gschemas.compiled

style: black

black:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run black $(MODULE)


checks: black-check flake8 pylint reno-lint

black-check:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run black --check $(MODULE) --extend-exclude $(MODULE)/_version.py

flake8:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run flake8 guake

pylint:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pylint --rcfile=.pylintrc --output-format=colorized $(MODULE)

sc: style check

dists: update-po requirements prepare-install rm-dists sdist bdist wheels
build: dists

sdist: generate-paths
	export SKIP_GIT_SDIST=1 && PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py sdist

rm-dists:
	rm -rf build dist

bdist: generate-paths
	# pipenv run python setup.py bdist
	@echo "Ignoring build of bdist package"

wheels: generate-paths
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py bdist_wheel

wheel: wheels

run-local: compile-glib-schemas-dev
ifdef V
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run ./scripts/run-local.sh -v
else
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run ./scripts/run-local.sh
endif

run-local-prefs: compile-glib-schemas-dev
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run ./scripts/run-local-prefs.sh

run-fr: compile-glib-schemas-dev
	LC_ALL=fr_FR.UTF8 PIPENV_IGNORE_VIRTUALENVS=1 pipenv run ./scripts/run-local.sh


shell:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv shell


test:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pytest $(MODULE)

test-actions:
	xvfb-run -a pipenv run pytest $(MODULE)
test-coverage:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run py.test -v --cov $(MODULE) --cov-report term-missing

test-pip-install-sdist: clean-pip-install-local generate-paths sdist
	@echo "Testing installation by pip (will install on ~/.local)"
	pip install --upgrade -vvv --user $(shell ls -1 dist/*.tar.gz | sort | head -n 1)
	ls -la ~/.local/share/guake
	~/.local/bin/guake

clean-pip-install-local:
	@rm -rfv ~/.local/guake
	@rm -rfv ~/.local/bin/guake
	@rm -rfv ~/.local/lib/python3.*/site-packages/guake
	@rm -rfv ~/.local/share/guake

test-pip-install-wheel: clean-pip-install-local generate-paths wheel
	@echo "Testing installation by pip (will install on ~/.local)"
	pip install --upgrade -vvv --user $(shell ls -1 dist/*.whl | sort | head -n 1)
	ls -la ~/.local/share/guake
	~/.local/bin/guake -v

sct: style check update-po requirements test


docs: clean-docs sdist
	cd docs && PIPENV_IGNORE_VIRTUALENVS=1 pipenv run make html

docs-open:
	xdg-open docs/_build/html/index.html

tag-pbr:
	@{ \
		set -e ;\
		export VERSION=$$(PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py --version | cut -d. -f1,2,3); \
		echo "I: Computed new version: $$VERSION"; \
		echo "I: presse ENTER to accept or type new version number:"; \
		read VERSION_OVERRIDE; \
		VERSION=$${VERSION_OVERRIDE:-$$VERSION}; \
		PROJECTNAME=$$(PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py --name); \
		echo "I: Tagging $$PROJECTNAME in version $$VERSION with tag: $$VERSION" ; \
		echo "$$ git tag $$VERSION -m \"$$PROJECTNAME $$VERSION\""; \
		git tag $$VERSION -m "$$PROJECTNAME $$VERSION"; \
		echo "I: Pushing tag $$VERSION, press ENTER to continue, C-c to interrupt"; \
		echo "$$ git push upstream $$VERSION"; \
	}
	@# Note:
	@# To sign, need gpg configured and the following command:
	@#  git tag -s $$VERSION -m \"$$PROJECTNAME $$VERSION\""

pypi-publish: build
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py upload -r pypi


update:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv update --clear
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv install --dev


lock: pipenv-lock requirements

requirements:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pipenv_to_requirements

pipenv-lock:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv lock


freeze:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run pip freeze


githook:
	bash git-hooks/post-commit

setup-githook:
	rm -f .git/hooks/post-commit
	cp -fv git-hooks/* .git/hooks/


push: githook
	git push origin --tags


clean: clean-ln-venv rm-dists clean-docs clean-po clean-schemas clean-py clean-paths uninstall-dev-locale
	@echo "clean successful"

clean-py:
	@pipenv --rm ; true
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -f $(DEV_DATA_DIR)/guake-prefs.desktop $(DEV_DATA_DIR)/guake.desktop
	@rm -rf .eggs *.egg-info po/*.pot

clean-paths:
	rm -f guake/paths.py guake/paths.py.dev

clean-po:
	@rm -f po/guake.pot
	@find po -name "*.mo" -exec rm -f {} \;

clean-docs:
	rm -rf doc/_build

update-po:
	echo "generating pot file"
	@find guake -iname "*.py" | xargs xgettext --from-code=UTF-8 --output=guake-python.pot
	@find $(DEV_DATA_DIR) -iname "*.glade" | sed -E "s#$(ROOT_DIR)/##g" | xargs xgettext --from-code=UTF-8 \
	                                                  -L Glade \
	                                                  --output=guake-glade.pot
	@(\
	    find $(DEV_DATA_DIR) -iname "*.desktop" | sed -E "s#$(ROOT_DIR)/##g" | xargs xgettext --from-code=UTF-8 \
		                                                  -L Desktop \
	                                                      --output=guake-desktop.pot \
	) || ( \
	    echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
	    touch guake-desktop.pot)
	@msgcat --use-first guake-python.pot guake-glade.pot guake-desktop.pot > po/guake.pot
	@rm guake-python.pot guake-glade.pot guake-desktop.pot
	@for f in $$(find po -iname "*.po"); do \
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
	@msgfmt --desktop --template=$(DEV_DATA_DIR)/guake.template.desktop \
		   -d po \
		   -o $(DEV_DATA_DIR)/guake.desktop || ( \
			   	echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
				cp $(DEV_DATA_DIR)/guake.template.desktop $(DEV_DATA_DIR)/guake.desktop)
	@msgfmt --desktop --template=$(DEV_DATA_DIR)/guake-prefs.template.desktop \
		   -d po \
		   -o $(DEV_DATA_DIR)/guake-prefs.desktop || ( \
			   	echo "Skipping .desktop files, is your gettext version < 0.19.1?" && \
				cp $(DEV_DATA_DIR)/guake-prefs.template.desktop $(DEV_DATA_DIR)/guake-prefs.desktop)

generate-paths:
	@echo "Generating path.py..."
	@cp -f guake/paths.py.in guake/paths.py
	@# Generic
	@sed -i -e 's|{{ LOGIN_DESTOP_PATH }}|""|g' guake/paths.py
	@sed -i -e 's|{{ AUTOSTART_FOLDER }}|""|g' guake/paths.py
	@# Dev environment:
	@sed -i -e 's|{{ LOCALE_DIR }}|get_default_locale_dir()|g' guake/paths.py
	@sed -i -e 's|{{ IMAGE_DIR }}|get_default_image_dir()|g' guake/paths.py
	@sed -i -e 's|{{ GUAKE_THEME_DIR }}|get_default_theme_dir()|g' guake/paths.py
	@sed -i -e 's|{{ GLADE_DIR }}|get_default_glade_dir()|g' guake/paths.py
	@sed -i -e 's|{{ SCHEMA_DIR }}|get_default_schema_dir()|g' guake/paths.py

reno:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run reno new $(SLUG) --edit

reno-lint:
	PIPENV_IGNORE_VIRTUALENVS=1 pipenv run reno -q lint

release-note: reno-lint release-note-news release-note-github

release-note-news: reno-lint
	@echo "Generating release note for NEWS file"
	@rm -f guake/releasenotes/notes/reno.cache
	@pipenv run python setup.py build_reno --output-file NEWS.rst.in
	@grep -v -R "^\.\.\ " NEWS.rst.in | cat -s > NEWS.rst
	@cat releasenotes/archive/NEWS.pre-3.0 >> NEWS.rst
	@rm -fv NEWS.rst.in
	@echo "Updated NEWS.rst"


release-note-github: reno-lint
	@echo
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "!! Generating release note for GitHub !!"
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "-------- copy / paste from here --------"
	@# markdown_github to be avoided => gfm output comes in pandoc 2.0.4 release dec 2017
	@pipenv run reno report 2>/dev/null | \
		pandoc -f rst -t markdown --markdown-headings=atx --wrap=none --tab-stop 2 | \
		tr '\n' '\r' | \
			sed 's/\r<!-- -->\r//g' | \
			sed 's/\r\-\ \r\r\ /\r-/g' | \
			sed 's/\r\ \ \:\ \ \ /\r    /g' | \
			sed 's/\r\r\ \ \ \ \-\ /\r    - /g' | \
			sed 's/\r\ \ \ \ \-\ /\r  - /g' | \
			sed 's/\r\ \ >\ \-\ /\r  - /g' | \
			sed 's/\\\#/\#/g' | \
		tr '\r' '\n'

release:
	git checkout -f master
	git pull --rebase upstream master
	@{ \
		set -e ;\
		export VERSION=$$(PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py --version | cut -d. -f1,2,3); \
		echo "I: Computed new version: $$VERSION"; \
		echo "I: presse ENTER to accept or type new version number:"; \
		read VERSION_OVERRIDE; \
		VERSION=$${VERSION_OVERRIDE:-$$VERSION}; \
		PROJECTNAME=$$(PIPENV_IGNORE_VIRTUALENVS=1 pipenv run python setup.py --name); \
		echo "I: Tagging $$PROJECTNAME in version $$VERSION with tag: $$VERSION" ; \
		echo "I: Pushing tag $$VERSION, press ENTER to continue, C-c to interrupt"; \
		git commit --all -m "Release $$VERSION" --allow-empty --no-edit ; \
		git tag $$VERSION -m "$$PROJECTNAME $$VERSION"; \
		make release-note-news rm-dists update-po dists ; \
		git commit --all --amend --no-edit; \
		git tag -f "$${VERSION}"; \
		make release-note-github; \
		echo ""; \
		echo "Please check your git history and push when ready with:"; \
		echo "  git push upstream master"; \
		echo "  git push upstream $$VERSION"; \
		echo ""; \
		echo "Revert with:"; \
		echo "  git tag -d $$VERSION"; \
	}


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
run-prefs: run-local-prefs
styles: style
uninstall: uninstall-system
upgrade: update
wheel: wheels
