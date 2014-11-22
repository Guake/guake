guakepyexecdir = $(pkgpyexecdir)
guakepyexec_LTLIBRARIES = globalhotkeys.la

globalhotkeys_la_SOURCES = \
	eggaccelerators.c \
	keybinder.c \
	globalhotkeys.c \
	eggaccelerators.h \
	keybinder.h

AM_CPPFLAGS = \
	$(DEPENDENCIES_CFLAGS) \
	$(PYTHON_CFLAGS)

AM_LDFLAGS = \
	-module -avoid-version \
	$(PYTHON_LIBS) $(DEPENDENCIES_LIBS)
