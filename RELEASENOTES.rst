=====
Guake
=====

.. _Guake_3.3.0:

3.3.0
=====

.. _Guake_3.3.0_New Features:

New Features
------------

.. releasenotes/notes/pip-a8c7f5e91190b7ba.yaml @ b'86995359b2ed76d582bf7db3e37a19be4d411314'

- ``pip install guake`` now compiles the gsettings schema and finds its languages automatically.


.. _Guake_3.3.0_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/wayland-3fcce3b30835e66d.yaml @ b'150a3a77f9355cb49e3c45a9be850b2f1ac684ec'

- Wayland is a bit more well supported. The X11 backend is now used by default for
  GDK and it seems to make the shortcut works under most situation.
  
  A more cleaner solution would be to develop a GAction
  (`vote for this feature here <https://feathub.com/Guake/guake/+29>`_])

.. releasenotes/notes/wayland-3fcce3b30835e66d.yaml @ b'150a3a77f9355cb49e3c45a9be850b2f1ac684ec'

- A new command has been added: ``guake-toggle``, should be faster than
  ``guake -t``. You can use it when you register the global shortcut manually
  (X11 or Wayland).


.. _Guake_3.2.2:

3.2.2
=====

.. _Guake_3.2.2_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/bugfix-b26aac4094ce8154.yaml @ b'48cf239e6accf9833926f2b9697731bfaca588aa'

- Fix transparency regression on ubuntu composite (#1333)

.. releasenotes/notes/bugfix-bb8c6dcf8cbd3b20.yaml @ b'2908357bf851063dbac7e813dfa746a06e0ba469'

- Fix transparency issue

.. releasenotes/notes/bugfix-bb8c6dcf8cbd3b20.yaml @ b'2908357bf851063dbac7e813dfa746a06e0ba469'

- Fix right-click on link

.. releasenotes/notes/bugfix-bb8c6dcf8cbd3b20.yaml @ b'2908357bf851063dbac7e813dfa746a06e0ba469'

- Fix bad css override on check tab background (#1326)

.. releasenotes/notes/bugfix-desktop-icon-68a8c2d6d2ef390c.yaml @ b'a4c9f1a74fb5e333ca0a789cce3189e5535ee390'

- Fix Guake application icon not displayed with German locale

.. releasenotes/notes/bugfix-f11b203584eeeb8e.yaml @ b'99ea0ab7ab8d14abb91d914da7bbc88d70411117'

- fix ctrl+click on hyperlinks on VTE 0.50 (#1295)

.. releasenotes/notes/palette-008d16139cff7b9c.yaml @ b'34b6259b388f44dab571e729ae1e9cc54d3d3b62'

- Fixed "Gruvbox Dark" color palette (swapped foreground and background)

.. releasenotes/notes/palette-ac719dfbd2dd49e9.yaml @ b'da0a5c25e7587292131895b34ff394e74075cd07'

- Swapped foreground and background colors for palettes added in commit #58842e9.


.. _Guake_3.2.2_Other:

Other
-----

.. releasenotes/notes/update-bootstrap-scripts-1ba9e40b4ab1bfd4.yaml @ b'2fa4c7b238babc6e9cd5869c47209ea6dad75014'

- Add option groupes to the bootstrap scripts


.. _Guake_3.2.1:

3.2.1
=====

.. _Guake_3.2.1_New Features:

New Features
------------

.. releasenotes/notes/palette-548f459256895a64.yaml @ b'de681c82ec77c7bebc9e23a76bf114641e8f5863'

- Thanks to @arcticicestudio, a new nice, clean new palette theme is available for Guake users:
  Nord (#1275)


.. _Guake_3.2.1_Known Issues:

Known Issues
------------

.. releasenotes/notes/hyperlinks-778efab6774df2e6.yaml @ b'3718a0a41c4c20bf3e966c48a9b3aefbe8874f0e'

- Multiline url are sometimes not handled correctly.

.. releasenotes/notes/translations-daa7e7aa85eec3bb.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- Users of Byobu or Tmux as default shell should disable the "login shell" option
  (in the "Shell" panel). This uses an option, ``--login``, that does not exist on these
  two tools.


.. _Guake_3.2.1_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/bugfix-5b330b910cf335bb.yaml @ b'9a53c4268b2764fb0a499405824e8adf967abdaf'

- Fix duplication in theme list (#1304)

.. releasenotes/notes/bugfix-ce7825d37bcf2273.yaml @ b'56f16c9b600fb2044b8d3db1fb6fe220438a258e'

- Fix right click selection in Midnight Commander

.. releasenotes/notes/fix-hyperlink-50901cd04a88876e.yaml @ b'fa20efa6d1530162f9c97f05d0552598a5d31afc'

- Corrected usage of ``Vte.Regex.new_for_match`` to fix regular expression matching
  (hyperlinks, quick open) on VTE >0.50 (#1295)

.. releasenotes/notes/hyperlinks-778efab6774df2e6.yaml @ b'3718a0a41c4c20bf3e966c48a9b3aefbe8874f0e'

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

.. releasenotes/notes/translations-daa7e7aa85eec3bb.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- Fix "Grubbox Dark" theme


.. _Guake_3.2.1_Translation Updates:

Translation Updates
-------------------

.. releasenotes/notes/translations-daa7e7aa85eec3bb.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- fr

.. releasenotes/notes/translations-daa7e7aa85eec3bb.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- pl

.. releasenotes/notes/translations-daa7e7aa85eec3bb.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- ru


.. _Guake_3.2.1_Other:

Other
-----

.. releasenotes/notes/docs-0c95ec1b74cc65d0.yaml @ b'352a2570ff7342a4a2cf53101b6afca7f6533e9e'

- Rework the documentation. The README grew up a lot and was hard to use. It has been cut into
  several user manual pages in the official online documentation.


.. _Guake_3.2.0:

3.2.0
=====

.. _Guake_3.2.0_New Features:

New Features
------------

.. releasenotes/notes/theme-1c1f13e63e46d98b.yaml @ b'0779655fd34df6fb98d1bb49db1cbd46d7b44d6d'

- Allow user to select the theme within the preference UI

.. releasenotes/notes/theme-a11c5b3cf19de34f.yaml @ b'21cf658bacd2b3559ebdb36a1527d0c3631e631f'

- Selected tab use "selected highlight" color from theme (#1036)


.. _Guake_3.2.0_Translation Updates:

Translation Updates
-------------------

.. releasenotes/notes/theme-1c1f13e63e46d98b.yaml @ b'0779655fd34df6fb98d1bb49db1cbd46d7b44d6d'

- fr


.. _Guake_3.1.1:

3.1.1
=====

.. _Guake_3.1.1_New Features:

New Features
------------

.. releasenotes/notes/quick-open-52d040f5e34e4d35.yaml @ b'8491450161e24cde0548a7e8541e85fb73ae0722'

- Quick open displays a combobox with predefined settings for Visual Studio Code, Atom and
  Sublime Text.


.. _Guake_3.1.1_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/bugfix-6096693463dd6c84.yaml @ b'8491450161e24cde0548a7e8541e85fb73ae0722'

- Fix  hyperlink VTE


.. _Guake_3.1.0:

3.1.0
=====

.. _Guake_3.1.0_Release Summary:

Release Summary
---------------

.. releasenotes/notes/install-b017d0fe51f8e2ad.yaml @ b'97bf2cb22586bde930ea12b3ebfbc1e611967359'


This version of Guake brings mostly bug fixes, and some new features like "Quick Open on selection". I have also reworked internally the Quick Open so that it can automatically open files from logs from pytest and other python development tools output.
However, there might still some false positive on the hovering of the mouse in the terminal, the most famous being the output of ``ls -l`` which may have the mouse looks like it sees hyperlinks on the terminal everywhere. Click does nothing but its an annoying limitation.
Package maintainers should read the "Notes for Package Maintainers" of this release note carefully.


.. _Guake_3.1.0_New Features:

New Features
------------

.. releasenotes/notes/autostart-300343bbe644bd7e.yaml @ b'ddc45d6d3359675b08b169585b97b51a1dc3b675'

- New "start at login" option in the settings (only for GNOME) #251

.. releasenotes/notes/debug-d435207215fdcc2e.yaml @ b'8f5a665141cc0c6951d81026a079762b0239851b'

- Add ``--verbose``/``-v`` parameter to enable debug logging. Please note the existing ``-v``
  (for version number) has been renamed ``-V``.

.. releasenotes/notes/hyperlink-e40e87ae4dc83c8e.yaml @ b'ed0278eba97a56a11b64050ef41e9c42c5ae19aa'

- Support for hyperlink VTE extension
  (`described here <https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda>`_ )
  #945 (Untested, as it requires VTE 0.50)

.. releasenotes/notes/palettes-ec272b2335a1fa06.yaml @ b'5065bd3f426ab77197f9c4ebd96bef11840f0a53'

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

.. releasenotes/notes/right-clic-f15043342128eb58.yaml @ b'0ff272c3f65ea9be7c5256962dbbf8be720f9763'

- Allow application to capture right click (ex: Midnight commander). #1096.
  It is still possible to show the contextual menu with Shift+right click.


.. _Guake_3.1.0_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/bugfix-78df60050b344c0b.yaml @ b'3dd342c500bda9e03400d30980481308b4e30472'

- delete tab even without libutempter (#1198)

.. releasenotes/notes/bugfix-abe62750f777873f.yaml @ b'b86c84922fe6d6485b5141b21bac9acd99884124'

- Fix crash when changing command file #1229

.. releasenotes/notes/bugfix-b54670a057197a9f.yaml @ b'347d02a69b1af3c0a3bf781d3d09ba5b7cc8a73d'

- fix ``import sys`` in ``simplegladeapp.py``

.. releasenotes/notes/bugfix_1225-6eecf165d1d0e732.yaml @ b'347d02a69b1af3c0a3bf781d3d09ba5b7cc8a73d'

- change scope of ``which_align`` variable in ``pref.py`` (#1225)

.. releasenotes/notes/quick_open-bb22f82761ad564b.yaml @ b'8274e950893f9ed119f88ca6b99ebe167571143c'

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

.. releasenotes/notes/translation-bd1cd0a5447ee42f.yaml @ b'56f16c9b600fb2044b8d3db1fb6fe220438a258e'

- Fix user interface translations #1228

.. releasenotes/notes/translation-ccde91d14559d6ab.yaml @ b'0d6bf217c40a522c23cc83a7e06ad98273cbe32b'

- Some systems such as Ubuntu did displayed Guake with a translated interface (#1209). The locale system has been reworked to fix that.

.. releasenotes/notes/translation-ccde91d14559d6ab.yaml @ b'0d6bf217c40a522c23cc83a7e06ad98273cbe32b'

- There might be broken translations, or not up-to-date language support by Guake. A global refresh of all existing translations would be welcomed. Most has not been updated since the transition to Guake 3, so these languages support might probably be unfunctional or at least partialy localized.

.. releasenotes/notes/translation-ccde91d14559d6ab.yaml @ b'0d6bf217c40a522c23cc83a7e06ad98273cbe32b'

- A big thank you for all the volunteers and Guake enthousiats would often update their own translation to help guake being used world-wide.
  - Help is always welcomed for updating translations !

.. releasenotes/notes/vte-d6fd6406c673f71a.yaml @ b'5e6339865120775e77436e03ed90cef6bc715dc9'

- Support for vte 2.91 (0.52) #1222


.. _Guake_3.1.0_Translation Updates:

Translation Updates
-------------------

.. releasenotes/notes/autostart-300343bbe644bd7e.yaml @ b'ddc45d6d3359675b08b169585b97b51a1dc3b675'

- fr_FR

.. releasenotes/notes/autostart-300343bbe644bd7e.yaml @ b'ddc45d6d3359675b08b169585b97b51a1dc3b675'

- pl

.. releasenotes/notes/update-de-translation-cfcb77e0e6b4543e.yaml @ b'2fe5656610a72d3a41fbf97c3e74a160b9821052'

- de


.. _Guake_3.1.0_Notes for Package Maintainers:

Notes for Package Maintainers
-----------------------------

.. releasenotes/notes/install-b017d0fe51f8e2ad.yaml @ b'97bf2cb22586bde930ea12b3ebfbc1e611967359'

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


.. _Guake_3.0.5:

3.0.5
=====

.. _Guake_3.0.5_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/bugfix-705c264a6b77f4d3.yaml @ b'45866977af61fdc18e2f8e4170ff6e8667ddea36'

- Apply cursor blinking to new tabs as well, not only on settings change.

.. releasenotes/notes/bugfix-c065e1a8b8e41270.yaml @ b'a17a2b5a4abcf18df96f83c1dca9f9519d75a5eb'

- Fix window losefocus hotkey #1080

.. releasenotes/notes/bugfix-cb51b18bfd3c8da3.yaml @ b'9465a191732f101891432bcdb70ce27cf6b37d8a'

- Fix refocus if open #1188

.. releasenotes/notes/fix-preference-window-header-color,-align-close-button-and-change-borders-to-margins-fa7ffffc45b12ea5.yaml @ b'2333606e7af3deb165bc8de23c392472420cf163'

- fix preferences window header color, align the close button more nicely and change borders to margins

.. releasenotes/notes/wayland-fa246d324c92fd80.yaml @ b'12a05905b2131dc091271cdf24b3c8b069da4cb0'

- Implements a timestamp for wayland (#1215)


.. _Guake_3.0.4:

3.0.4
=====

.. _Guake_3.0.4_New Features:

New Features
------------

.. releasenotes/notes/Add-window-displacement-options-to-move-guake-away-from-the-edges-1b2d46997e8dbe91.yaml @ b'93099961f7c90a22089b76a8a9acf1414bea56e5'

- Add window displacement options to move guake away from the screen edges

.. releasenotes/notes/Add-window-displacement-options-to-move-guake-away-from-the-edges-1b2d46997e8dbe91.yaml @ b'93099961f7c90a22089b76a8a9acf1414bea56e5'

- User can manually enter the name of the GTK theme it wants Guake to use. Note there is no
  Preference settings yet, one needs to manually enter the name using ``dconf-editor``, in the
  key ``/apps/guake/general/gtk-theme-name``. Use a name matching one the folders in
  ``/usr/share/themes``. Please also considere this is a early adopter features and has only
  been tested on Ubuntu systems.
  Dark theme preference can be se with the key ``/apps/guake/general/gtk-prefer-dark-theme``.

.. releasenotes/notes/fix-make-install-system-as-non-root-user-40cdbb0509660741.yaml @ b'7fb39459c9dd852411fcd968fcfbbf33f5bfa4ca'

- Allow make install-system to be run as non root user and print a message if so.

.. releasenotes/notes/quick_open-032209b39bb6831f.yaml @ b'4423af1c134e80a81e4c68fdcf5eea2ade969c74'

- Quick open can now open file under selection. Simply select a filename in the current terminal
  and do a Ctrl+click, if the file path can be found, it will be open in your editor. It allows
  to virtually open any file path in your terminal (if they are on your local machine), but
  requires the user to select the file path first, compared to the Quick Open feature that
  finds file names using regular expression.
  
  Also notes that is it able to look in the current folder if the selected file name exists,
  allowing Ctrl+click on relative paths as well.
  
  Line number syntax is also supported: ``filename.txt:5`` will directly on the 5th line if
  your Quick Open is set for.


.. _Guake_3.0.4_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/Add-window-displacement-options-to-move-guake-away-from-the-edges-1b2d46997e8dbe91.yaml @ b'93099961f7c90a22089b76a8a9acf1414bea56e5'

- fixes issue with vertically stacked dual monitors #1162

.. releasenotes/notes/bugfix-654583b5646cf905.yaml @ b'1367a6b7cdf856efea50e0956f894be088d1f681'

- Quick Open functionnality is restored #1121

.. releasenotes/notes/bugfix-90bd70c984ad6a73.yaml @ b'69ae4fe8036eae8e2f7418cd08fccb95fe41eb07'

- Unusable Guake with "hide on focus lose" option #1152

.. releasenotes/notes/dbus-c3861541c24b328a.yaml @ b'c0443dd7df49346a87f1fa08a52c1c6f76727ad8'

- Speed up guake D-Bus communication (command line such as ``guake -t``).


.. _Guake_3.0.3:

3.0.3
=====

.. _Guake_3.0.3_Release Summary:

Release Summary
---------------

.. releasenotes/notes/gtk3-a429d01811754c42.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

This minor release mainly focus on fixing big problems that was remaining after the migration to GTK3. I would like to akwonledge the work of some contributors that helped testing and reporting issues on Guake 3.0.0. Thanks a lot to @egmontkob and @aichingm.


.. releasenotes/notes/prefs-032d2ab0c8e2f17a.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

The Preference window has been deeply reworked and the hotkey management has been rewriten. This was one the the major regression in Guake 3.0.


.. _Guake_3.0.3_New Features:

New Features
------------

.. releasenotes/notes/auto-edit-648e3609c9aee103.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- [dev env] automatically open reno slug after creation for editing

.. releasenotes/notes/dev-env-fb2967d1ba8ee495.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- [dev env]: Add the possibility to terminate guake with ``Ctrl+c`` on terminal
  where Guake has been launched

.. releasenotes/notes/scroll-959087c80640ceaf.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Add "Infinite scrolling" option in "Scrolling" panel #274

.. releasenotes/notes/show-focus-cab5307b44905f7e.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Added hotkey for showing and focusing Guake window when it is opened or closed.
  It is convenient when Guake window are overlapped with another windows and user
  needs to just showing it without closing and opening it again. #1133


.. _Guake_3.0.3_Known Issues:

Known Issues
------------

.. releasenotes/notes/packages-55d1017dd708b8de.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- Quick Edit feature is not working (#1121)


.. _Guake_3.0.3_Deprecations:

Deprecations
------------

.. releasenotes/notes/visible-bell-12de7acf136d3fa4.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Remove visible bell feature #1081


.. _Guake_3.0.3_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/fix-guake-showing-up-on-startup-0fdece37dc1616e4.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Command options do not work, crash when disabling keybinding #1111

.. releasenotes/notes/fix-guake-showing-up-on-startup-0fdece37dc1616e4.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Do not open Guake window upon startup #1113

.. releasenotes/notes/fix-in/decrease-height-8176a8313d9a1aba.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Fix crash on increase/decrease main window height shortcut #1099

.. releasenotes/notes/fix-rename-tab-shortcut-62ad1410c2958929.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Resolved conflicting default shortcut for ``Ctrl+F2`` (now, rename current tab is set to
  ``Ctrl+Shift+R``) #1101, #1098

.. releasenotes/notes/hotkeys-42708e8968fd7b25.yaml @ b'41c5b8b408b0360483f2e467f616f88a534acf83'

- The hotkey management has been rewriten and is now fully functional

.. releasenotes/notes/prefs-032d2ab0c8e2f17a.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Rework the Preference window and reorganize the settings. Lot of small issues
  has been fixed.
  The Preference window now fits in a 1024x768 screen.

.. releasenotes/notes/run-command-517683bd988aa06a.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Fix 'Failed to execute child process "-"' - #1119

.. releasenotes/notes/scroll-959087c80640ceaf.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- History size spin is fixed and now increment by 1000 steps. Default history value is now set to
  1000, because "1024" has no real meaning for end user. #1082


.. _Guake_3.0.3_Translation Updates:

Translation Updates
-------------------

.. releasenotes/notes/translation-31e67dc4190a9067.yaml @ b'7cb971cf125e41f6294b8b17003276abb18a8734'

- de

.. releasenotes/notes/translation-31e67dc4190a9067.yaml @ b'7cb971cf125e41f6294b8b17003276abb18a8734'

- fr

.. releasenotes/notes/translation-31e67dc4190a9067.yaml @ b'7cb971cf125e41f6294b8b17003276abb18a8734'

- ru


.. _Guake_3.0.3_Other:

Other
-----

.. releasenotes/notes/packages-55d1017dd708b8de.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- The dependencies of the Guake executable has been slightly better described in README.
  There is an example for Debian/Ubuntu in the file ``scripts/bootstrap-dev-debian.sh`` which is
  the main environment where Guake is developed and tested.

.. releasenotes/notes/packages-55d1017dd708b8de.yaml @ b'40849130c85207d03bd077270ff09e632aa1cd58'

- Package maintainers are encouraged to submit their ``bootstrap-dev-[distribution].sh``,
  applicable for other distributions, to help users install Guake from source, and other package
  maintainers.


.. _Guake_3.0.2:

3.0.2
=====

.. _Guake_3.0.2_New Features:

New Features
------------

.. releasenotes/notes/dark_theme-4bb6be4b2cfd92ae.yaml @ b'b0f73e5d93f3b688cf311f5925eb0c95d8cc64e4'

- Preliminary Dark theme support. To use it, install the 'numix' theme in your system.
  For example, Ubuntu/Debian users would use ``sudo apt install numix-gtk-theme``.


.. _Guake_3.0.2_Known Issues:

Known Issues
------------

.. releasenotes/notes/dark_theme-4bb6be4b2cfd92ae.yaml @ b'b0f73e5d93f3b688cf311f5925eb0c95d8cc64e4'

- Cannot enable or disable the GTK or Dark theme by a preference setting.


.. _Guake_3.0.2_Deprecations:

Deprecations
------------

.. releasenotes/notes/resizer-d7c6553879852019.yaml @ b'4b50f6714f56e72b38856ec1933790c5624e3399'

- Resizer discontinued


.. _Guake_3.0.2_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/make-096ad37e6079df09.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Fix ``sudo make uninstall/install`` to work only with ``/usr/local``

.. releasenotes/notes/make-096ad37e6079df09.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Fix translation ``mo`` file generation

.. releasenotes/notes/make-096ad37e6079df09.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- Fix crash on Wayland

.. releasenotes/notes/match-b205323a7aa019f9.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Fix quick open and open link in terminal

.. releasenotes/notes/not_composited_de-505082d1c18eda3c.yaml @ b'6459a2c14fd5366fae5d245aac9df21e7e7955dc'

- Fixed Guake initialization on desktop environment that does not support compositing.


.. _Guake_3.0.1:

3.0.1
=====

.. _Guake_3.0.1_Release Summary:

Release Summary
---------------

.. releasenotes/notes/maintenance-e02e946e15c940ab.yaml @ b'5cbf4cf065f11067118430eda32cb2fcb5516874'

Minor maintenance release.


.. _Guake_3.0.1_Bug Fixes:

Bug Fixes
---------

.. releasenotes/notes/maintenance-e02e946e15c940ab.yaml @ b'5cbf4cf065f11067118430eda32cb2fcb5516874'

- Code cleaning and GNOME desktop file conformance


.. _Guake_3.0.0:

3.0.0
=====

.. _Guake_3.0.0_Release Summary:

Release Summary
---------------

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

Guake has been ported to GTK-3 thanks to the huge work of @aichingm. This also implies Guake now uses the latest version of the terminal emulator component, VTE 2.91.
Guake is now only working on Python 3 (version 3.5 or 3.6). Official support for Python 2 has been dropped.
This enables new features in upcoming releases, such as "find in terminal", or "split screen".


.. _Guake_3.0.0_New Features:

New Features
------------

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

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

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Guake now use a brand new build system:
  
    - ``pipenv`` to manage dependencies in `Pipfile`
    - enforced code styling and checks using Pylint, Flake8, Yapf, ISort.
    - simpler release management thanks to PBR

.. releasenotes/notes/reno-3b5ad9829b256250.yaml @ b'8ea70114fc51ffef8436da8cde631a8246cc6794'

- [dev env] `reno <https://docs.openstack.org/reno/latest/>`_ will be used to generate
  release notes for Guake starting version 3.0.0.
  It allows developers to write the right chunk that will appear in the release
  note directly from their Pull Request.

.. releasenotes/notes/update-window-title-c6e6e3917821902d.yaml @ b'7bea32df163cde90d4aeca26a58305fc2db05bfd'

- Update Guake window title when:
  
    - the active tab changes
    - the active tab is renamed
    - the vte title changes


.. _Guake_3.0.0_Known Issues:

Known Issues
------------

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Translation might be broken in some language, waiting for the translation file to be updated by volunteers

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Resizer does not work anymore

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Package maintainers have to rework their integration script completely

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- quick open and open link in terminal is broken

.. releasenotes/notes/update-window-title-c6e6e3917821902d.yaml @ b'7bea32df163cde90d4aeca26a58305fc2db05bfd'

- **Note for package maintainers**: Guake 3 has a minor limitation regarding Glib/GTK Schemas
  files. Guake looks for the gsettings schema inside its data directory. So you will probably
  need install the schema twice, once in ``/usr/local/lib/python3.5/dist-packages/guake/data/``
  and once in ``/usr/share/glib-2.0/schemas`` (see
  `#1064 <https://github.com/Guake/guake/issues/1064>`_).
  This is planned to be fixed in Guake 3.1


.. _Guake_3.0.0_Upgrade Notes:

Upgrade Notes
-------------

.. releasenotes/notes/pref-af8621e5c04d973c.yaml @ b'5f6952a8385f93bfc649b434b6e4728b046f714d'

- Minor rework of the preference window.


.. _Guake_3.0.0_Deprecations:

Deprecations
------------

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Background picture is no more customizable on each terminal

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- Visual Bell has been deprecated


.. _Guake_3.0.0_Translation Updates:

Translation Updates
-------------------

.. releasenotes/notes/gtk3-800a345dfd067ae6.yaml @ b'dcb33c0f7048f5c96c2d13f747bbd686c65dd91d'

- fr-FR

