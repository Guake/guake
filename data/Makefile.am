SUBDIRS = pixmaps icons

man_MANS = guake.1

uidir = $(datadir)/guake
ui_DATA = \
	about.glade \
	guake.glade \
	prefs.glade

# dbus service file
servicedir = $(datadir)/dbus-1/services
service_in_files = org.guake.Guake.service.in
service_DATA = $(service_in_files:.service.in=.service)

@INTLTOOL_DESKTOP_RULE@
desktopdir = $(datadir)/applications
desktop_in_files = guake.desktop.in guake-prefs.desktop.in
desktop_DATA = $(desktop_in_files:.desktop.in=.desktop)

@INTLTOOL_SCHEMAS_RULE@
schemadir = $(GCONF_SCHEMA_FILE_DIR)
schema_DATA = guake.schemas

EXTRA_DIST = \
	$(ui_DATA) \
	$(schema_DATA) \
	$(desktop_in_files) \
	$(man_MANS)

if GCONF_SCHEMAS_INSTALL
install-data-local:
	-GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
	$(GCONFTOOL) --makefile-install-rule $(schema_DATA)
endif

if GCONF_SCHEMAS_INSTALL
uninstall-local:
	-GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) \
	$(GCONFTOOL) --makefile-uninstall-rule $(schema_DATA)
endif
