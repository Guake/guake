=====
Guake
=====

3.6.3
=====

New Features
------------

- Add drag-n-drop to terminal (text & uris)

- When scrolling with "shift" (1 page) or "shift + ctrl" (4 pages) it will be faster (#271)

Bug Fixes
---------

- Add schema_version check for tabs session restore

- Add save/restore terminal split for tabs session - Save/Restore terminal split by pre-order traversal full binary tree in list

- Bump tabs session schema_version to 2 (to support terminal split)

- Lazy restore terminal split until Guake is visible

- Manage terminal signal handler by handler_ids

- Avoid spurious resize event when showing fullscreened window

- Make sure workspace-specific-tab-sets only enable on X11 backend (due to wnck)

- Add install/uninstall-dev-locale to support dev locale

- Fix DualTerminalBox grab focus when remove dead child

- Support customize prefix for make

- Fix re-focus on terminal after rename dialog destroy

- Fix split terminal by menu will not follow last terminal cwd (if option set)

- Fix delete_shell using os.waitpid (should not use it)

Translation Updates
-------------------

- German

- French

3.6.2
=====

Bug Fixes
---------

- Respect the XDG Base Directory Specification by supporting ``XDG_CONFIG_HOME``
  environment variable to find the ``~/.config`` directory.

Translation Updates
-------------------

- Czech (thanks @p-bo)

- Dutch (thanks @Vistaus)

- Norwegian Bokmål (thanks @comradekingu)

- Polish (thanks @piotrdrag)

- Russian (thanks @f2404)

Notes for Package Maintainers
-----------------------------

- The ``data`` directory is back into ``guake`` module, in order to prepare for
  the migration to importlib-resource (#1405). This should simplify a lot
  the load of resources, and avoid all the complication due to difference in
  prod/dev/traditional linux/debian customization/...

3.6.1
=====

Bug Fixes
---------

- Fix search box background so that it will follow current theme

- Minor build system fixes

3.6.0
=====

Release Summary
---------------

This release brings three of the most awaited features on Guake:

   - search in current terminal
   - session saving
   - settings export and import

Our MVC ("Most Valuable Contributor") for this release is Louie Lu (@mlouielu) who worked hard to build these three features in a row! Thank you very much for your hard work !

New Features
------------

- Add --support option to Guake CLI for user when need to report issue

- Add save/restore tabs function.

- Add label parameter to ``notebook.new_page_with_focus``

- Add search box for terminal. Default hotkey is ``Ctrl+Shift+F``.

- Add session save preferences for startup/tabs:
  
    - "restore-tabs-startup": when enabled, it will restore tabs when startup
    - "restore-tabs-notify": when enabled, it will notify user after tabs restored (except startup)
    - "save-tabs-when-changed": when enabled, it will automatically save tabs session
      when changed (new/del/reorder)

- Add CLI option to split tab: ``--split-vertical`` and ``--split-horizontal``.

- Save and restore Guake settings

Bug Fixes
---------

- Add libwnck to bootstrap scripts

- Fix a need for double toggling to hide when using command line with ``--show`` and option with ``only_show_hide = False``.

- Remove unused logging level setup

- Fix window-title-changed didn't save tabs

- fix typo

- Fix ``vte-warning`` when using ``Vte.Regex.new_for_match``

- Workspaces can now properly save/restore tabs

- Fix ``on_terminal_title_changed`` only searching in current_notebook (it should find every notebook)

Translation Updates
-------------------

- fr (French)

- pl (Polish)

- added zh_TW (Chinese Traditional). Louie Lu would be very glad to have some help on localizing Guake!

- ru (Russian)

- nb (Norvegian)

- sv (Swedish)

- nl (Dutch)

Notes for Package Maintainers
-----------------------------

- Package maintainers should be aware that ``libwnck`` (Window Navigator Construction Kit)
  is now a mandatory dependency of Guake.

3.5.0
=====

Release Summary
---------------

This version is mainly a maintaince release, after the big reworks on Guake from last year. I took some delay in fixing Guake due to a growing family.
Thanks again for the various contributors who submitted their patches, it helps a lot the whole community. I may be able to find more time in the upcoming months to add even cooler features to our beloved Guake.

New Features
------------

- new hotkey (CTRL+SHIFT+H) to open new tab in home directory

- "New tab" button #1471

- Open new tab by double-clicking on the tab bar

- Add new context menu on the notebook

- Add a CLI option to change palette scheme #1345

- Bold text is also bright (>= VTE 0.52 only)

- `guake --split-vertical` and `--split-horizontal` split the current
   tab just like the context menu does

- Optional close buttons for tabs (disabled by default)

- Guake can now provide a set of tabs per workspace

Bug Fixes
---------

- Reverse transparency slider (to be more meaningful, #1501

- Fix command-line select tab behavior #1492

- removed duplicate event bind? previously I had issue where quick-open event would be fired 
  twice because of this.

- fixes

- fixes

- fix unnecessary show/hide

- fix settings only applied to the active workspace if more the 1 is used

- fix prompt quit dialog numbers when more then 1 workspace is used

Translation Updates
-------------------

- fr

- de

Other
-----

- For `Guake translators using weblate <https://hosted.weblate.org/projects/guake/guake/>`_,
  I had to force push because of big conflicts. Some may have loose recent translation in your
  language. Sorry for that.

3.4.0
=====

Release Summary
---------------

This major release provides one of the most awaited feature to every Guake adicts: Split terminal. Split easily vertically and horizontally each terminal and have more than one terminal per tab.
There have been several shortcut changes to help navigate easily on your screen: Ctrl+Shift+Up/Down/Left/Right to switch from terminal to terminal.
Thanks for you hard work, @aichingm !

New Features
------------

- Split and resize terminals via mouse or keyboard shortcuts.

Deprecations
------------

- "New terminal" / "Rename terminal" / "Close terminal" items has been removed from the
  terminal context menu. They are still available on the tab context menu.

Bug Fixes
---------

- Fix multiline selection right click (#1413)

- Fix tab name (#1017)

- fixes jumping preference window (#1149)

- fix no focus after closing a split terminal (#1421)

- Add note about shell that does not support --login parameter (#469)

Translation Updates
-------------------

- pl (Piotr Drąg on weblate)

- nl (Heimen Stoffels on weblate)

- nb (Allan Nordhøy on weblate)

- ru (Igor on weblate)

- zh_CN (庄秋彬 on weblate)

- cs (Pavel Borecki on weblate)

- de (Robin Bauknecht on weblate)

- fr (Gaetan Semet)

3.3.3
=====

Release Summary
---------------

This release adds a big rewrite of the Terminal underlying mechanism by Mario Aichinger. It will serve as a foundation layer for long-awaiting features such as `Split Terminal <https://github.com/Guake/guake/issues/71>`_, `Find Text <https://github.com/Guake/guake/issues/116>`_, `Save/Load Session <https://github.com/Guake/guake/issues/114>`_, and so on.

New Features
------------

- add a new option in the context menu (copy url)

- support for per terminal context menus

- new more fullscreen handeling

- load default font via python Gio and not via cli call

- add json example for custom commands in the code

- port screen selectino (use_mouse) to Gdk

- add notification for failed show-hide key rebindings

- add one-click key binding editing

- port word character exceptions for newer vte versions

- use Gtk.Box instead of Gtk.HBox

- use Gtk.Notebook's tabs implementation

- enable tab switching by scrolling (mouse wheel) over the tabs/tab-bar

Bug Fixes
---------

- fixes Settings schema 'guake.general' does not contain a key named 'display_n'

- fixes ``guake --fgcolor/--bgcolor`` error (#1376).

Translation Updates
-------------------

- fr (thanks samuelorsi125t and ButterflyOfFire)

- ru (thanks Igor)

- pl (thanks Piotr Drąg)

- cz (thanks Pavel Borecki)

- de (thanks Dirk den Hoedt and Mario Aichinger)

- gl (thanks Nacho Vidal)

Notes for Package Maintainers
-----------------------------

- Please note ``libutempter0`` should now be considered as a mandatory dependency of Guake.
  It solves the frozen terminal issue on exit (#1014)

3.3.2
=====

Bug Fixes
---------

- Travis build cleaned build artifacts before deployment, leading to missing files when
  built in the CI.

3.3.1
=====

Release Summary
---------------

This minor release mainly fix some issues when installing Guake though ``pip install --user --upgrade guake``.
A big thanks also to everyone who contributed to the translations on `Weblate <https://hosted.weblate.org/projects/guake/guake/>`_.

Bug Fixes
---------

- Don't translate application icon (this finally fixes Guake application icon not being displayed with German locale, which was only partially resolved with #1320)

- Install of Guake through pip install was broken (missing ``paths.py``). Now fixed. Discarded generation of bdist. (fix

Translation Updates
-------------------

- sv (thanks to @MorganAntonsson)

- de (thanks to @rzimmer)

- fr

- ru (thanks Igor "f2404" on Weblate)

- cz (thanks Pavel Borecki on Weblate)

- pl (thanks Piotr Drąg on Weblate)

- it (thanks Maurizio De Santis on Weblate)

Other
-----

- Update about screen's credits

3.3.0
=====

New Features
------------

- ``pip install guake`` now compiles the gsettings schema and finds its languages automatically.

Bug Fixes
---------

- Wayland is a bit more well supported. The X11 backend is now used by default for
  GDK and it seems to make the shortcut works under most situation.
  
  A more cleaner solution would be to develop a GAction
  (`vote for this feature here <https://feathub.com/Guake/guake/+29>`_])

- A new command has been added: ``guake-toggle``, should be faster than
  ``guake -t``. You can use it when you register the global shortcut manually
  (X11 or Wayland).

3.2.2
=====

Bug Fixes
---------

- Fix transparency regression on ubuntu composite (#1333)

- Fix transparency issue

- Fix right-click on link

- Fix bad css override on check tab background (#1326)

- Fix Guake application icon not displayed with German locale

- fix ctrl+click on hyperlinks on VTE 0.50 (#1295)

- Fixed "Gruvbox Dark" color palette (swapped foreground and background)

- Swapped foreground and background colors for palettes added in commit #58842e9.

Other
-----

- Add option groupes to the bootstrap scripts

3.2.1
=====

New Features
------------

- Thanks to @arcticicestudio, a new nice, clean new palette theme is available for Guake users:
  Nord (#1275)

Known Issues
------------

- Multiline url are sometimes not handled correctly.

- Users of Byobu or Tmux as default shell should disable the "login shell" option
  (in the "Shell" panel). This uses an option, ``--login``, that does not exist on these
  two tools.

Bug Fixes
---------

- Fix duplication in theme list (#1304)

- Fix right click selection in Midnight Commander

- Corrected usage of ``Vte.Regex.new_for_match`` to fix regular expression matching
  (hyperlinks, quick open) on VTE >0.50 (#1295)

- URL with ``'`` (simple quote) and ``()`` (parenthesis) are now captured by hyperlink matcher.
  This may causes some issues with log and so that use parenthesis *around* hyperlinks,
  but since parenthesis and quotes are valid characters inside a URL, like for instance
  URL created by Kibana, they deserve the right to be shown as proper url in Guake.
  
  User can still select the URL in the terminal if he wishes to capture the exact url, before
  doing a Ctrl+click or a right click.
  
  For developers, it is advised to end the URL with a character that cannot be used in URL, such
  as space, tab, new line. Ending with a dot (``.``) or a comma (``,``) will not be seen as part
  of the URL by Guake, so most logs and traces that adds a dot or a comma at the end of the URL
  might still work.

- Fix "Grubbox Dark" theme

Translation Updates
-------------------

- fr

- pl

- ru

Other
-----

- Rework the documentation. The README grew up a lot and was hard to use. It has been cut into
  several user manual pages in the official online documentation.

3.2.0
=====

New Features
------------

- Allow user to select the theme within the preference UI

- Selected tab use "selected highlight" color from theme (#1036)

Translation Updates
-------------------

- fr

3.1.1
=====

New Features
------------

- Quick open displays a combobox with predefined settings for Visual Studio Code, Atom and
  Sublime Text.

Bug Fixes
---------

- Fix  hyperlink VTE

3.1.0
=====

Release Summary
---------------

This version of Guake brings mostly bug fixes, and some new features like "Quick Open on selection". I have also reworked internally the Quick Open so that it can automatically open files from logs from pytest and other python development tools output.
However, there might still some false positive on the hovering of the mouse in the terminal, the most famous being the output of ``ls -l`` which may have the mouse looks like it sees hyperlinks on the terminal everywhere. Click does nothing but its an annoying limitation.
Package maintainers should read the "Notes for Package Maintainers" of this release note carefully.

New Features
------------

- New "start at login" option in the settings (only for GNOME) #251

- Add ``--verbose``/``-v`` parameter to enable debug logging. Please note the existing ``-v``
  (for version number) has been renamed ``-V``.

- Support for hyperlink VTE extension
  (`described here <https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda>`_ )
  #945 (Untested, as it requires VTE 0.50)

- Add great color palettes from
  `Guake Color Scheme <https://github.com/ziyenano/Guake-Color-Schemes>`_, thanks for @ziyenano :
  
    - `Aci`,
    - `aco`,
    - `Azu`,
    - `Bim`,
    - `Cai`,
    - `Elementary`,
    - `Elic`,
    - `Elio`,
    - `Freya`,
    - `Gruvbox Dark`,
    - `Hemisu Dark`,
    - `Hemisu Light`,
    - `Jup`,
    - `Mar`,
    - `Material`,
    - `Miu`,
    - `Monokai dark`,
    - `Nep`,
    - `One Light`,
    - `Pali`,
    - `Peppermint`,
    - `Sat`,
    - `Shel`,
    - `Tin`,
    - `Ura`,
    - `Vag`.

- Allow application to capture right click (ex: Midnight commander). #1096.
  It is still possible to show the contextual menu with Shift+right click.

Bug Fixes
---------

- delete tab even without libutempter (#1198)

- Fix crash when changing command file #1229

- fix ``import sys`` in ``simplegladeapp.py``

- change scope of ``which_align`` variable in ``pref.py`` (#1225)

- Fix several issues on Quick Edit:
  
  - quick open freezes guake
  - support for systems with PCRE2 (regular expression in terminal) disabled for VTE, like
    Ubuntu 17.10 and +.
  
    This might disable quick open and open url on direct Ctrl+click.
    User can still select the wanted url or text and Cltr+click or use contextual menu.
  
    See this `discussion on Tilix <https://github.com/gnunn1/tilix/issues/916>`_, another
    Terminal emulator that suffurs the same issue.
  
  - quick open now appears in contextual menu (#1157)
  - bad translation update on the contextual menu. This causes new strings that was hidden to
    appear for translators.
  - Fix quick open on pattern "File:line" line that was not opening the wanted file.

- Fix user interface translations #1228

- Some systems such as Ubuntu did displayed Guake with a translated interface (#1209). The locale system has been reworked to fix that.

- There might be broken translations, or not up-to-date language support by Guake. A global refresh of all existing translations would be welcomed. Most has not been updated since the transition to Guake 3, so these languages support might probably be unfunctional or at least partialy localized.

- A big thank you for all the volunteers and Guake enthousiats would often update their own translation to help guake being used world-wide.
  - Help is always welcomed for updating translations !

- Support for vte 2.91 (0.52) #1222

Translation Updates
-------------------

- fr_FR

- pl

- de

Notes for Package Maintainers
-----------------------------

- The setup mecanism has changed a little bit. Some maintainers used to patch the source code
  of Guake to change the pixmap, Gtk schema or locale paths directly in the ``guake/globals.py``
  file. This was due to a lack of flexibility of the installation target of the ``Makefile``.
  
  The ``make install`` target looks now a little bit more familiar, allowing distribution
  packager to set the various paths directly with make flags.
  
  For example:
  
  .. code-block:: bash
  
      sudo make install \
          prefix=/usr \
          DESTDIR=/path/for/packager \
          PYTHON_SITE_PACKAGE_NAME=site-package \
          localedir=/usr/share/locale
  
  The main overrides are:
  
  - ``IMAGE_DIR``: where the pixmap should be installed. Default: ``/usr/local/share/guake/pixmaps``
  - ``localedir``: where locales should be installed. Default: ``/usr/local/share/locale``
  - ``GLADE_DIR``: where the Glade files should be installed. Default: ``/usr/local/share/guake``
  - ``gsettingsschemadir``: where gsettings/dconf schema should be installed.
    Default: ``/usr/local/share/glib-2.0/schemas/``
  
  I invite package maintainers to open tickets on Github about any other difficulties
  encountered when packaging Guake.

3.0.5
=====

Bug Fixes
---------

- Apply cursor blinking to new tabs as well, not only on settings change.

- Fix window losefocus hotkey #1080

- Fix refocus if open #1188

- fix preferences window header color, align the close button more nicely and change borders to margins

- Implements a timestamp for wayland (#1215)

3.0.4
=====

New Features
------------

- Add window displacement options to move guake away from the screen edges

- User can manually enter the name of the GTK theme it wants Guake to use. Note there is no
  Preference settings yet, one needs to manually enter the name using ``dconf-editor``, in the
  key ``/apps/guake/general/gtk-theme-name``. Use a name matching one the folders in
  ``/usr/share/themes``. Please also considere this is a early adopter features and has only
  been tested on Ubuntu systems.
  Dark theme preference can be se with the key ``/apps/guake/general/gtk-prefer-dark-theme``.

- Allow make install-system to be run as non root user and print a message if so.

- Quick open can now open file under selection. Simply select a filename in the current terminal
  and do a Ctrl+click, if the file path can be found, it will be open in your editor. It allows
  to virtually open any file path in your terminal (if they are on your local machine), but
  requires the user to select the file path first, compared to the Quick Open feature that
  finds file names using regular expression.
  
  Also notes that is it able to look in the current folder if the selected file name exists,
  allowing Ctrl+click on relative paths as well.
  
  Line number syntax is also supported: ``filename.txt:5`` will directly on the 5th line if
  your Quick Open is set for.

Bug Fixes
---------

- fixes issue with vertically stacked dual monitors #1162

- Quick Open functionnality is restored #1121

- Unusable Guake with "hide on focus lose" option #1152

- Speed up guake D-Bus communication (command line such as ``guake -t``).

3.0.3
=====

Release Summary
---------------

This minor release mainly focus on fixing big problems that was remaining after the migration to GTK3. I would like to akwonledge the work of some contributors that helped testing and reporting issues on Guake 3.0.0. Thanks a lot to @egmontkob and @aichingm.

The Preference window has been deeply reworked and the hotkey management has been rewriten. This was one the the major regression in Guake 3.0.

New Features
------------

- [dev env] automatically open reno slug after creation for editing

- [dev env]: Add the possibility to terminate guake with ``Ctrl+c`` on terminal
  where Guake has been launched

- Add "Infinite scrolling" option in "Scrolling" panel #274

- Added hotkey for showing and focusing Guake window when it is opened or closed.
  It is convenient when Guake window are overlapped with another windows and user
  needs to just showing it without closing and opening it again. #1133

Known Issues
------------

- Quick Edit feature is not working (#1121)

Deprecations
------------

- Remove visible bell feature #1081

Bug Fixes
---------

- Command options do not work, crash when disabling keybinding #1111

- Do not open Guake window upon startup #1113

- Fix crash on increase/decrease main window height shortcut #1099

- Resolved conflicting default shortcut for ``Ctrl+F2`` (now, rename current tab is set to
  ``Ctrl+Shift+R``) #1101, #1098

- The hotkey management has been rewriten and is now fully functional

- Rework the Preference window and reorganize the settings. Lot of small issues
  has been fixed.
  The Preference window now fits in a 1024x768 screen.

- Fix 'Failed to execute child process "-"' - #1119

- History size spin is fixed and now increment by 1000 steps. Default history value is now set to
  1000, because "1024" has no real meaning for end user. #1082

Translation Updates
-------------------

- de

- fr

- ru

Other
-----

- The dependencies of the Guake executable has been slightly better described in README.
  There is an example for Debian/Ubuntu in the file ``scripts/bootstrap-dev-debian.sh`` which is
  the main environment where Guake is developed and tested.

- Package maintainers are encouraged to submit their ``bootstrap-dev-[distribution].sh``,
  applicable for other distributions, to help users install Guake from source, and other package
  maintainers.

3.0.2
=====

New Features
------------

- Preliminary Dark theme support. To use it, install the 'numix' theme in your system.
  For example, Ubuntu/Debian users would use ``sudo apt install numix-gtk-theme``.

Known Issues
------------

- Cannot enable or disable the GTK or Dark theme by a preference setting.

Deprecations
------------

- Resizer discontinued

Bug Fixes
---------

- Fix ``sudo make uninstall/install`` to work only with ``/usr/local``

- Fix translation ``mo`` file generation

- Fix crash on Wayland

- Fix quick open and open link in terminal

- Fixed Guake initialization on desktop environment that does not support compositing.

3.0.1
=====

Release Summary
---------------

Minor maintenance release.

Bug Fixes
---------

- Code cleaning and GNOME desktop file conformance

3.0.0
=====

Release Summary
---------------

Guake has been ported to GTK-3 thanks to the huge work of @aichingm. This also implies Guake now uses the latest version of the terminal emulator component, VTE 2.91.
Guake is now only working on Python 3 (version 3.5 or 3.6). Official support for Python 2 has been dropped.
This enables new features in upcoming releases, such as "find in terminal", or "split screen".

New Features
------------

- Ported to GTK3:
  
    - cli arguments
    - D-Bus
    - context menu of the terminal, the tab bar and the tray icon
    - scrollbar of the terminal
    - ``ctrl+d`` on terminal
    - fix double click on the tab bar
    - fix double click on tab to rename
    - fix clipboard from context menu
    - notification module
    - keyboard shortcuts
    - preference screen
    - port ``gconfhandler`` to ``gsettingshandler``
    - about dialog
    - pattern matching
    - ``Guake.accel*`` methods

- Guake now use a brand new build system:
  
    - ``pipenv`` to manage dependencies in `Pipfile`
    - enforced code styling and checks using Pylint, Flake8, Yapf, ISort.
    - simpler release management thanks to PBR

- [dev env] `reno <https://docs.openstack.org/reno/latest/>`_ will be used to generate
  release notes for Guake starting version 3.0.0.
  It allows developers to write the right chunk that will appear in the release
  note directly from their Pull Request.

- Update Guake window title when:
  
    - the active tab changes
    - the active tab is renamed
    - the vte title changes

Known Issues
------------

- Translation might be broken in some language, waiting for the translation file to be updated by volunteers

- Resizer does not work anymore

- Package maintainers have to rework their integration script completely

- quick open and open link in terminal is broken

- **Note for package maintainers**: Guake 3 has a minor limitation regarding Glib/GTK Schemas
  files. Guake looks for the gsettings schema inside its data directory. So you will probably
  need install the schema twice, once in ``/usr/local/lib/python3.5/dist-packages/guake/data/``
  and once in ``/usr/share/glib-2.0/schemas`` (see
  `#1064 <https://github.com/Guake/guake/issues/1064>`_).
  This is planned to be fixed in Guake 3.1

Upgrade Notes
-------------

- Minor rework of the preference window.

Deprecations
------------

- Background picture is no more customizable on each terminal

- Visual Bell has been deprecated

Translation Updates
-------------------

- fr-FR



Version 0.8.11
--------------

Maintainance release with bug fixes and translation updates.

- #885 revert to the old fixed-width tabs behavior
- move the startup script setting to the hooks tab
- #977 Add a configuration toggle to disable windows refocus
- #970 Right-click tab options don't work properly
- #995 Russian translation
- #983 French translation
- #986 Update German translation


Version 0.8.10
--------------

Minors Bug fixes and new Ocean and Oceanic Next color schemes.


Version 0.8.9
-------------

Thanks for guakers for the following contibutions:

New features:

- #793, #876: Execute a script on display event
- #864: Add preference dialog checkbox for toggling 'resizer' visibility
- #885: tabs share the full screen width
- #942: Quick open also matches `/home` path
- #933: Add `-l` option to get tab label

Bug Fixes

- #934: Quick open does not work with dash
- #893, #896, #888: another Unity screen size fix
- Translation update: ja (#875), cn (#955), nl (#931), pt (#895),


Version 0.8.8
-------------

Thank to these contribution from Guake users, I am happy to announce a new minor fix release of
Guake.

Features:

* Close a tab with the middle button of the mouse

Bug Fixes:

- Fix error when toggle key was disabled
- Update change news
- Uppercase pallete name
- Fix pylint errors
- Convert README badge to SVG
- Update Japanese translation
- update Russian translation
- updated CS translation
- Update zh_CN translation


Version 0.8.7
-------------

Do not forget to update the software version

Version 0.8.6
-------------

Lot of bug fixes in this release. Thanks for all contributors !

Please note that it is not tested on dual screen set ups.

Bug fixes:

* Terminal geometry fixes (#773 @koter84, #775 RedFlames, b36295 myself)
* Fix "changing max tab length" set all tab to same title
* Fix on terminal kill (#636, @coderstephen)
* Typo/Cosmetics (#761, @thuandt)
* Fix the bottom of tab buttons being cut off in Gnome (#786 @lopsided98)
* Fix fullscreen follow mouse (#774 @koter84)
* Option to shorten VTE tab name (#798 @versusvoid)
* Updated translations:

  - french (b071b4, myself)
  - russian (#787 @vantu5z),
  - corean (#766 @nessunkim),
  - polish (#799 @piotrdrag)



Version 0.8.5
-------------

Minor version today, mostly minor bug fixes and translation update.

I did have time to work on GTK3, maintaining Guake to keep using GTK2 is more and more difficult,
Travis kind of abandonned the compatibility of PyGtk2.

* Add a shortcut to open the last tab (#706, thanks @evgenius)
* Fix icon size on Ubuntu (#734)
* Add tab UUID and selection by UUID (#741, thanks @SoniEx2, @Ozzyboshi)
* Updated Polish (#705), Chinese (#711), German (#732), Brazil Portuguese (#744), Czech (#747)
* Fixed doc (#709, #706)
* Fix some Pep8 issue



Version 0.8.4
-------------

Bug fixes:

 - Very big icon tray (#598, @thardev)
 - Feature keyboard shorcut hide on lose focus (#650, #262, #350, @thardev)
 - Endless transparency and small rework of hide on lose focus (#651, @thardev)
 - fix tray icon does not align in center (#663, @wuxinyumrx)
 - Updated pt_BR translation (#686, @matheus-manoel)
 - improved Bluloco theme readability (#693, @uloco)
 - ensure gsettings process is well kill (#636)
 - fix exception in preference panel



Version 0.8.3
-------------

Quick fix about missing svg file


Version 0.8.2
-------------

Bug fix version. Thanks for external contributions!

Feature:

- new palette 'Bluloco' (my default one now!) (@uloco)

Bug fixes:

- tab bar width (@ozzyboshi)
- open new tab in current directory (#578, @Xtreak)
- fix default interpreter (#619, @Xtreak)
- fix use VTE title (#524, @Xtreak)
- Russian tranlation (@vantu5z), german (@Airfunker), spanish (@thardev) chinese (@Xinyu Ng)
- fix guake cannot restore fullscreen (#628, @thardev)


Version 0.8.1
-------------

  I started working on Guake 1.0.0, and not in a dedicated branch. It is now in its own source
  folder. We clearly need to move to gtk3 soon, since GTK2 is being discontinued, the VTE is no more
  maintained for GTK2-Python, and adds lot of cool features.

  So I am now starting to work on a complete rewrite of Guake, so don't expect 0.8.x to see lot of
  new features, unfortunately. But Guake 1.0.0 will add features such as:

   - line wrap in terminal
   - search in terminal
   - dconf/gsettings to store configuration
   - GTK3 look and feel
   - much cleaner build and translation systems

  But, this means I cannot work too much on 0.8.x. I still do some bug fixes, and thanks to external
  contributors that share the love for Guake, Guake 0.8 still moves on!

  So don't hesitate to have a look in the code to fix any bug you are experiencing and submit a Pull
  Request.

  New features:

  - a-la guake-indicator custom commands (#564) - by @Ozzyboshi!
  - Add option to allow/disallow bold font (#603) - by @helix84!
  - Clean current terminal item in contextual menu (#608) - by @Denis Subbotin

  Bug fixes:

  - Terminal widget disappears at random times (#592)
  - Typo - by @selivan, @Ruined1


Version 0.8.0
-------------

  I have been extremely busy the previous 3 months, so I have almost not worked on Guake. I wanted
  to introduce in the next version some major features heavily asked, like session save and split
  terminal. They will have to wait a bit more.

  As a result, most of the contribution are from external contributors. Thank you very much for all
  these patches!

  This releases introduces two major changes in the project, thus the minor version change.

  First, the new homepage is now online:

    http://guake-project.org/

  As I remind you, Guake has *not* control over the old domain guake.org. So far the content is
  still one of the old content of this domain. So please use http://guake-project.org to reference
  Guake.

  Source code of the Web site can be found here:

    https://github.com/Guake/guake-website

  The second major change in the project is the abandon of our internal hotkey manager
  ``globalhotkey``, which was responsible for binding hotkeys globally to the window manager. This
  piece of code was extremely old and hard to maintain. This was also unnecessarily complexifying
  the build process of Guake. Thanks to the contribution of @jenrik, we are now using a pretty
  common package ``keybinder`` (Ubuntu: ``python-keybinder``).

  Bug fixes:


  - Guake fails to start due to a GlobalHotkey related C call fixed by replacing GlobalHotkeys with
    keybinder. Fixed by @jenrik. (#558, #510)
  - Fix icon issue with appindicator (#591)
  - swap terms correctly when moving tabs (#473, #512, #588)
  - Remove last reference to --show-hide (#587)
  - fixed and completed german translation (#585)
  - Drop duplicated man page (a526046a)
  - use full path to tray icon with libappindicator (#591)


Version 0.7.2 (2015.05.20)
--------------------------

  Bug fixes:

  - Fix Ctrl+D regresion (#550)
  - update Quick Open Preference Window


Version 0.7.1 (2015.05.18):
---------------------------

  Some bug fixes, and cleared issues with new palette colors.

  As side note, our domain 'guake.org' has been squatted by an outsider that seems only interested
  in getting money to release the domain. Since Guake is a small project, based on 100% OpenSource
  spirit, we do not want to loose more time on this subject. The guake website will be deployed soon
  on a new URL:

      http://guake-project.org

  Please do **NOT** use guake.org anymore, until we can retrieve it. We cannot be hold responsible
  for any content on guake.org anymore.

  Bug fixes:

  - Background and font color inversed for some color schemes (#516)
  - Guake width wrong on non-Unity Ubuntu desktop (#517)
  - Add get_gtktab_name dbus interface (#529, #530)
  - Fix issue with selection copy (#514)
  - I18n fixes and updated Polish translation (#519). Thanks a lot @piotrdrag!
  - Remove add and guake icon in tab (#543)
  - prompt_on_close_tab option (#546) Thanks a lot @tobz1000!
  - Fix default shortcuts for move tabs


Version 0.7.0 (2015.05.02):
---------------------------

  I had more time working on Guake recently, so I fixed some long term issues, and exposed some
  internal settings into the preference window.

  Thanks for the external contribution: @varemenos, @seraff and others!

  Here is the complete changelog for this release:

  - Reorganised palette definition, add a demo terminal in preference panel (#504, #273, #220)
  - Plenty of other new color palettes (thanks again @varemenos ! #504)
  - don't propagate COLORTERM environment variable in terminal (#488)
  - Force $TERM environment variable to 'xterm-256color' in terminals (#341)
  - Fix issue with the quit confirmation dialog box (#499)
  - Add shortcut for transparency level (#481)
  - Add label to tell user how to disable a shortcut (#488)
  - Expose cursor_shape and blink cursor method in pref window (#505)
  - Expose Guake startup script to the pref window (#198)
  - Some window management bug fixes (#506, #445)
  - Fix "Not focused on openning if tab was moved" (#441)
  - Add contextual menu item 'Open Link' on right click on a link (5476653)
  - Fix compatibility with Ubuntu 15.04 (#509)
  - Fix Guake Turns Gray sometimes (#473, #512)


Version 0.6.2 (2015.04.20):
---------------------------
  - Packaging issue fixes


Version 0.6.1 (2015.04.19):
---------------------------
  - bug fixes


Version 0.6.0 (2015.04.18):
---------------------------
  This version is poor in new feature, I just don't have time to work on Guake. I got a lot of
  incompatibility reports on new systems, such as Wayland. Port to gtk3 is still a must have, but
  all features of the VTE component does not seem to have been ported.

  Features:

   - Save current terminal buffer to file
   - Hotkeys for moving tab
   - plenty of color palettes (thanks @varemenos !)
   - bug fixes


Version 0.5.2 (2014.11.23):
---------------------------

 - bug fixes
 - Disable the 'focus_if_open' feature (hidden trigger, true per default). Restaure focus does not
   work in all systems.
 - lot of "componentization" of the code, in preparation to the rebase of 'gtk3' branch.


Version 0.5.1 (2014.11.06):
---------------------------

  - minor bug fixes release


Version 0.5.0 (2014.02.22):
---------------------------

  - Tab can be moved
  - Add change tab hotkey (F1-F10 by default) and is display on tab
  - Add "New tab" menu item
  - Quick open file path within the terminal output
  - gconf only settings:

     - startup scripts
     - vertical aligments

  - minor bug fixes
  - New maintainer:

    * Gaetan Semet <gaetan@xeberon.net>

  - Contributors:

    * @koter84
    * @kneirinck


Versions < 0.5.0
----------------

changes since 0.4.4:

  - Custom tab titles are no longer overriden by VTE ones (rgaudin)
  - Absent notifications daemon is no longer fatal
  - Fix for <Ctrl>key hotkeys being recorded as <Primary>key (Ian MacLeod)
  - Font resizing using <Ctrl>+ and <Ctrl>- (Eiichi Sato)
  - D-Bus and commandline interface improvements
  - L10n:

    * Norwegian Bokmål po file renamed to nb_NO.po (Bjørn Lie)
    * Added translations: Croatian, Czech, Dutch, Galician, Indonesian, Ukrainian.
    * Updated translations: Catalan, French, German, Hungarian, Spanish, Swedish.

changes since 0.4.3:

  - New icon for both guake and guake-prefs
  - Improved build scripts for themable icon installation
  - Updated some autotools files
  - Fixing a typo in the guake-prefs.desktop file (Zaitor)
  - wm_class can't be get by gnome-shell css #414
  - Add the missing "System" category required by FDO menu specification (Jekyll Wu)
  - Do not install the system-wide autostart file (Jekyll Wu)
  - Call window.move/resize only when not in fullscreen mode #403 (Empee584)
  - Terminal scrolls to the wrong position when hiding and unhiding in fullscreen mode #258
    (Empee584)
  - Toggle fullscreen malfunction #371 (Empee584 & Sylvestre)
  - Guake overlaped the second screen in a dual-monitor setup with a sidepanel (Sylvestre)
  - Tree items in Keyboard shortcuts tab of preferences window not localized #280 (Robertd)
  - Add option to start in fullscreen mode #408 (Dom Sekotill)
  - Refactoring of the fullscreen logic and addition of the --fullscreen flag (Marcel Partap)

changes since 0.4.2:

  - Better tab titling, based on VTE title sequences (Aleksandar Krsteski & Max Ulidtko)
  - Some drag & drop support (Max Ulidtko)
  - Fix for the many times reported "gconf proxy port as int" issue (Pingou)
  - Better file layout which doesn't modify PYTHONPATH (Max Ulidtko)

Updated translation and new translation:

  - Russian (Vadim Kotov)
  - Spanish (Ricardo A. Hermosilla Carrillo)
  - Japanese (kazutaka)
  - Catalan (el_libre como el chaval)

changes since 0.4.1:

Updated translations and new translations (unsorted):

  - Norwegian (wty)
  - Turkish (Berk Demirkır)
  - Swedish (Daniel Nylander)
  - Persian (Kasra Keshavarz)
  - French (Bouska and Pingou)
  - Russian (Pavel Alexeev and vkotovv)
  - Polish (Piotr Drąg)
  - Spanish, Castilian (dmartinezc)
  - Italian (Marco Leogrande a.k.a. dark)
  - Chinese simplified (甘露, Gan Lu)
  - Portuguese/Brazilian (Djavan Fagundes)
  - Japanese (kazutaka)
  - Punjabi (A S Alam)

Bugs/Features:

  - Calling the hide() method when closing main window: #229 (Lincoln)
  - Fixing dbus path and name for the RemoteControl object: #202 (Lincoln)
  - Setting http{s,}_proxy vars before calling fork_command: #172 (Lincoln)
  - Adding the `fr' lang to ALL_LINGUAS: #189 (Lincoln)
  - Option to configure the color palette: #51 (Eduardo Grajeda)
  - Do not hide when showing rename dialog (Aleksandar Krsteski)
  - Fixing the tab renaming feature: #205 (Lincoln)

changes since 0.4.0:

Updated translation and new translation:

  - Italian
  - French
  - Portuguese/Brazilian
  - Novergian
  - German
  - Polish
  - Greek
  - Hungarian

Bugs/Features:

  - Change start message #168
  - Add an option to the preference windows to create new tab in cwd #146
  - Preferences windows are resizable #149
  - Guake's windows not shown when ran for the first time #174
  - Implement dbus interface to script with guake #150, #138, #105, #126, #128, #109
  - Command line arguments implemented -n create a new tab -e execute a command on a defined tab -r
    rename a tab -t toggle visibility
  - Improve regex to use character classes (improve the support of certain locales) #156
  - Ask user if he really wants to quit when there is a child process #158
  - Double click on a tab allows you to rename the tab #165
  - Add more information on the INSTALL file
  - Tray icon position fixed #161

Infrastructure:

  - Move from guake-terminal.org to guake.org
  - Set up a mailing-list at: http://lists.guake.org/cgi-bin/mailman/listinfo/guake

changes since 0.2

    * Making prefs dialog window better, including a better title, fixing some paddings and spaces.
    * Added backspace and delete compatibility options (thanks to gnome-terminal guys =)
    * Cleanup of data files (images and glade files), mostly images.
    * Complete rewrite of tab system in the main window.
    * Fixing all issues (I think =) in close tab feature.
    * Adding tab rename feature.
    * Making easier to grab keybinging shortcuts from the prefs screen by using eggcellrendererkeys
      lib.
    * Now we look for more python interpreters when filling interpreters combo.
    * Fixing a lot of bugs.
