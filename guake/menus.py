import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from locale import gettext as _
gi.require_version('Vte', '2.91')  # vte-0.42
from gi.repository import Vte
from guake.customcommands import CustomCommands

import logging
log = logging.getLogger(__name__)


def mk_tab_context_menu(callback_object):
    """Create the context menu for a notebook tab
    """
    # Store the menu in a temp variable in terminal so that popup() is happy. See:
    #   https://stackoverflow.com/questions/28465956/
    callback_object.context_menu = Gtk.Menu()
    menu = callback_object.context_menu
    mi1 = Gtk.MenuItem(_("New Tab"))
    mi1.connect("activate", callback_object.on_new_tab)
    menu.add(mi1)
    mi2 = Gtk.MenuItem(_("Rename"))
    mi2.connect("activate", callback_object.on_rename)
    menu.add(mi2)
    mi3 = Gtk.MenuItem(_("Close"))
    mi3.connect("activate", callback_object.on_close)
    menu.add(mi3)
    menu.show_all()
    return menu


def mk_notebook_context_menu(callback_object):
    """Create the context menu for the notebook
    """
    callback_object.context_menu = Gtk.Menu()
    menu = callback_object.context_menu
    mi = Gtk.MenuItem(_("New Tab"))
    mi.connect("activate", callback_object.on_new_tab)
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.ImageMenuItem("gtk-preferences")
    mi.set_use_stock(True)
    mi.connect("activate", callback_object.on_show_preferences)
    menu.add(mi)
    mi = Gtk.ImageMenuItem("gtk-about")
    mi.set_use_stock(True)
    mi.connect("activate", callback_object.on_show_about)
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.MenuItem(_("Quit"))
    mi.connect("activate", callback_object.on_quit)
    menu.add(mi)
    menu.show_all()
    return menu


SEARCH_SELECTION_LENGTH = 20
FILE_SELECTION_LENGTH = 30


def mk_terminal_context_menu(terminal, window, settings, callback_object):
    """Create the context menu for a terminal.
    """
    # Store the menu in a temp variable in terminal so that popup() is happy. See:
    #   https://stackoverflow.com/questions/28465956/
    terminal.context_menu = Gtk.Menu()
    menu = terminal.context_menu
    mi = Gtk.MenuItem(_("Copy"))
    mi.connect("activate", callback_object.on_copy_clipboard)
    menu.add(mi)
    if get_link_under_cursor(terminal) is not None:
        mi = Gtk.MenuItem(_("Copy Url"))
        mi.connect("activate", callback_object.on_copy_url_clipboard)
        menu.add(mi)
    mi = Gtk.MenuItem(_("Paste"))
    mi.connect("activate", callback_object.on_paste_clipboard)
    # check if clipboard has text, if not disable the paste menuitem
    clipboard = Gtk.Clipboard.get_default(window.get_display())
    mi.set_sensitive(clipboard.wait_is_text_available())
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.MenuItem(_("Toggle Fullscreen"))
    mi.connect("activate", callback_object.on_toggle_fullscreen)
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.MenuItem(_("Split ―"))
    mi.connect("activate", callback_object.on_split_horizontal)
    menu.add(mi)
    mi = Gtk.MenuItem(_("Split ｜"))
    mi.connect("activate", callback_object.on_split_vertical)
    menu.add(mi)
    mi = Gtk.MenuItem(_("Close terminal"))
    mi.connect("activate", callback_object.on_close_terminal)
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.MenuItem(_("Save content..."))
    mi.connect("activate", callback_object.on_save_to_file)
    menu.add(mi)
    mi = Gtk.MenuItem(_("Reset terminal"))
    mi.connect("activate", callback_object.on_reset_terminal)
    menu.add(mi)
    # TODO SEARCH uncomment menu.add()
    mi = Gtk.MenuItem(_("Find..."))
    mi.connect("activate", callback_object.on_find)
    # menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.MenuItem(_("Open link..."))
    mi.connect("activate", callback_object.on_open_link)
    link = get_link_under_cursor(terminal)
    # TODO CONTEXTMENU this is a mess Quick open should also be sensible
    # if the text in the selection is a url the current terminal
    # implementation does not support this at the moment
    if link:
        if len(link) >= FILE_SELECTION_LENGTH:
            mi.set_label(_("Open Link: {!s}...").format(link[:FILE_SELECTION_LENGTH - 3]))
        else:
            mi.set_label(_("Open Link: {!s}").format(link))
        mi.set_sensitive(True)
    else:
        mi.set_sensitive(False)
    menu.add(mi)
    mi = Gtk.MenuItem(_("Search on Web"))
    mi.connect("activate", callback_object.on_search_on_web)
    selection = get_current_selection(terminal, window)
    if selection:
        search_text = selection.rstrip()
        if len(search_text) > SEARCH_SELECTION_LENGTH:
            search_text = search_text[:SEARCH_SELECTION_LENGTH - 3] + "..."
        mi.set_label(_("Search on Web: '%s'") % search_text)
        mi.set_sensitive(True)
    else:
        mi.set_sensitive(False)
    menu.add(mi)
    mi = Gtk.MenuItem(_("Quick Open..."))
    mi.connect("activate", callback_object.on_quick_open)
    if selection:
        filename = get_filename_under_cursor(terminal, selection)
        if filename:
            filename_str = str(filename)
            if len(filename_str) > FILE_SELECTION_LENGTH:
                mi.set_label(
                    _("Quick Open: {!s}...").format(filename_str[:FILE_SELECTION_LENGTH - 3])
                )
            else:
                mi.set_label(_("Quick Open: {!s}").format(filename_str))
            mi.set_sensitive(True)
        else:
            mi.set_sensitive(False)
    else:
        mi.set_sensitive(False)
    menu.add(mi)
    customcommands = CustomCommands(settings, callback_object)
    if customcommands.should_load():
        submen = customcommands.build_menu()
        if submen:
            menu.add(Gtk.SeparatorMenuItem())
            mi = Gtk.MenuItem(_("Custom Commands"))
            mi.set_submenu(submen)
            menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.ImageMenuItem("gtk-preferences")
    mi.set_use_stock(True)
    mi.connect("activate", callback_object.on_show_preferences)
    menu.add(mi)
    mi = Gtk.ImageMenuItem("gtk-about")
    mi.set_use_stock(True)
    mi.connect("activate", callback_object.on_show_about)
    menu.add(mi)
    menu.add(Gtk.SeparatorMenuItem())
    mi = Gtk.ImageMenuItem(_("Quit"))
    mi.connect("activate", callback_object.on_quit)
    menu.add(mi)
    menu.show_all()
    return menu


def get_current_selection(terminal, window):
    if terminal.get_has_selection():
        terminal.copy_clipboard()
        clipboard = Gtk.Clipboard.get_default(window.get_display())
        return clipboard.wait_for_text()
    return None


def get_filename_under_cursor(terminal, selection):
    filename, _1, _2 = terminal.is_file_on_local_server(selection)
    log.info("Current filename under cursor: %s", filename)
    if filename:
        return filename
    return None


def get_link_under_cursor(terminal):
    link = terminal.found_link
    log.info("Current link under cursor: %s", link)
    if link:
        return link
    return None
