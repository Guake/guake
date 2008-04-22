@INTLTOOL_XML_RULE@
@INTLTOOL_DESKTOP_RULE@

SUBDIRS = pixmaps

uidir = $(datadir)/guake
ui_DATA = \
	about.glade \
	guake.glade \
	prefs.glade

# .desktop file
Multimediadir = $(datadir)/applications
Multimedia_in_files = guake.desktop
Multimedia_DATA = $(Multimedia_in_files:.desktop.in=.desktop)

# dbus service file
servicedir = $(datadir)/dbus-1/services
service_in_files = org.gnome.Guake.service.in
service_DATA = $(service_in_files:.service.in=.service)

# schema file.
# not using GCONF_SCHEMA_FILE_DIR because it is
# sending our schemafile to /usr dir =/
schemadir = $(sysconfdir)/gconf/schemas
schema_DATA = guake.schemas

if GCONF_SCHEMAS_INSTALL
install-data-local: $(schema_DATA)
	GCONF_CONFIG_SOURCE=$(GCONF_SCHEMA_CONFIG_SOURCE) $(GCONFTOOL) --makefile-install-rule $(srcdir)/$(schema_DATA);
endif

EXTRA_DIST = $(ui_DATA) \
			 $(schema_DATA) \
			 guake.desktop.in

