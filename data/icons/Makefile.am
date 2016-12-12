iconthemedir = $(datadir)/icons/hicolor

appsicon16dir = $(iconthemedir)/16x16/apps
appsicon22dir = $(iconthemedir)/22x22/apps
appsicon24dir = $(iconthemedir)/24x24/apps
appsicon32dir = $(iconthemedir)/32x32/apps
appsicon48dir = $(iconthemedir)/48x48/apps
appsicon256dir = $(iconthemedir)/256x256/apps

dist_appsicon16_DATA = 16x16/apps/guake.png 16x16/apps/guake-prefs.png
dist_appsicon22_DATA = 22x22/apps/guake.png 22x22/apps/guake-prefs.png
dist_appsicon24_DATA = 24x24/apps/guake.png 24x24/apps/guake-prefs.png
dist_appsicon32_DATA = 32x32/apps/guake.png 32x32/apps/guake-prefs.png
dist_appsicon48_DATA = 48x48/apps/guake.png 48x48/apps/guake-prefs.png
dist_appsicon256_DATA = 256x256/apps/guake.png 256x256/apps/guake-prefs.png

update_icon_cache = gtk-update-icon-cache --ignore-theme-index --force

install-data-hook: install-update-icon-cache
uninstall-hook: uninstall-update-icon-cache

install-update-icon-cache:
	$(AM_V_at)$(POST_INSTALL)
	test -n "$(DESTDIR)" || $(update_icon_cache) "$(iconthemedir)"

uninstall-update-icon-cache:
	$(AM_V_at)$(POST_UNINSTALL)
	test -n "$(DESTDIR)" || $(update_icon_cache) "$(iconthemedir)"

EXTRA_DIST = source.svg
