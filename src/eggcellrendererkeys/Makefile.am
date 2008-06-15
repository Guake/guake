cellrendererkeysdir = $(libdir)/guake
lib_LTLIBRARIES = cellrendererkeys.la

cellrendererkeys_la_LDFLAGS = \
	-module \
	-avoid-version \
	-export-symbols-regex initcellrendererkeys

cellrendererkeys_la_LIBADD = \
	$(PYTHON_LIBS) \
	$(DEPENDENCIES_LIBS)

cellrendererkeys_la_CPPFLAGS = \
	$(PYTHON_CFLAGS) \
	$(DEPENDENCIES_CFLAGS) \
	-DEGG_COMPILATION

cellrendererkeys_la_SOURCES = \
	cellrendererkeysmodule.c \
	eggcellrendererkeys.c eggcellrendererkeys.h \
	eggaccelerators.c eggaccelerators.h

nodist_cellrendererkeys_la_SOURCES = cellrendererkeys.c

EXTRA_DIST = cellrendererkeys.defs cellrendererkeys.override

cellrendererkeys.c: cellrendererkeys.defs cellrendererkeys.override
CLEANFILES = cellrendererkeys.c

.defs.c:
	(cd $(srcdir)\
	 && $(PYGTK_CODEGEN) \
	    --load-types eggcellrendererkeys-arg-types.py \
            --override $*.override \
            --prefix py$* $*.defs) > gen-$*.c \
        && cp gen-$*.c $*.c \
        && rm -f gen-$*.c
