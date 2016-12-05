from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import gconf
import gtk
import logging
import subprocess

from pango import FontDescription
from xml.sax.saxutils import escape as xml_escape

import guake.notifier

from guake.common import _
from guake.common import pixmapfile
from guake.globals import GCONF_PATH
from guake.globals import GKEY
from guake.globals import KEY
from guake.globals import LKEY


GCONF_MONOSPACE_FONT_PATH = '/desktop/gnome/interface/monospace_font_name'
DCONF_MONOSPACE_FONT_PATH = 'org.gnome.desktop.interface'
DCONF_MONOSPACE_FONT_KEY = 'monospace-font-name'


log = logging.getLogger(__name__)


class GConfHandler(object):

    """Handles gconf changes, if any gconf variable is changed, a
    different method is called to handle this change.
    """

    def __init__(self, guake):
        """Constructor of GConfHandler, just add the guake dir to the
        gconf client and bind the keys to its handler methods.
        """
        self.guake = guake

        client = gconf.client_get_default()
        client.add_dir(GCONF_PATH, gconf.CLIENT_PRELOAD_RECURSIVE)

        notify_add = client.notify_add

        # these keys does not need to be watched.
        # notify_add(KEY('/general/default_shell'), self.shell_changed)
        # notify_add(KEY('/general/use_login_shell'), self.login_shell_toggled)
        # notify_add(KEY('/general/use_popup'), self.popup_toggled)
        # notify_add(KEY('/general/window_losefocus'), self.losefocus_toggled)
        # notify_add(KEY('/general/use_vte_titles'), self.use_vte_titles_changed)
        # notify_add(KEY('/general/quick_open_enable'), self.on_quick_open_enable_changed)
        # notify_add(KEY('/general/quick_open_in_current_terminal'),
        #   self.on_quick_open_in_current_terminal_changed)

        # Notification is not required for mouse_display/display_n because
        # set_final_window_rect polls gconf and is called whenever Guake is
        # shown or resized

        notify_add(KEY('/general/show_resizer'), self.show_resizer_toggled)

        notify_add(KEY('/general/use_trayicon'), self.trayicon_toggled)
        notify_add(KEY('/general/window_ontop'), self.ontop_toggled)
        notify_add(KEY('/general/tab_ontop'), self.tab_ontop_toggled)
        notify_add(KEY('/general/window_tabbar'), self.tabbar_toggled)
        notify_add(KEY('/general/window_height'), self.size_changed)
        notify_add(KEY('/general/window_width'), self.size_changed)
        notify_add(KEY('/general/window_height_f'), self.size_changed)
        notify_add(KEY('/general/window_width_f'), self.size_changed)
        notify_add(KEY('/general/window_valignment'), self.alignment_changed)
        notify_add(KEY('/general/window_halignment'), self.alignment_changed)
        notify_add(KEY('/style/cursor_blink_mode'), self.cursor_blink_mode_changed)
        notify_add(KEY('/style/cursor_shape'), self.cursor_shape_changed)

        notify_add(KEY('/general/use_scrollbar'), self.scrollbar_toggled)
        notify_add(KEY('/general/history_size'), self.history_size_changed)
        notify_add(KEY('/general/scroll_output'), self.keystroke_output)
        notify_add(KEY('/general/scroll_keystroke'), self.keystroke_toggled)

        notify_add(KEY('/general/use_default_font'), self.default_font_toggled)
        notify_add(KEY('/general/use_palette_font_and_background_color'),
                   self.palette_font_and_background_color_toggled)
        notify_add(KEY('/style/font/style'), self.fstyle_changed)
        notify_add(KEY('/style/font/color'), self.fcolor_changed)
        notify_add(KEY('/style/font/palette'), self.fpalette_changed)
        # notify_add(KEY('/style/font/palette_name'), self.fpalette_changed)
        notify_add(KEY('/style/font/allow_bold'), self.allow_bold_toggled)
        notify_add(KEY('/style/background/color'), self.bgcolor_changed)
        notify_add(KEY('/style/background/image'), self.bgimage_changed)
        notify_add(KEY('/style/background/transparency'),
                   self.bgtransparency_changed)

        notify_add(KEY('/general/compat_backspace'), self.backspace_changed)
        notify_add(KEY('/general/compat_delete'), self.delete_changed)
        notify_add(KEY('/general/custom_command_file'), self.custom_command_file_changed)
        notify_add(KEY('/general/max_tab_name_length'), self.max_tab_name_length_changed)
        notify_add(KEY('/general/abbreviate_tab_names'), self.abbreviate_tab_names_changed)

    def custom_command_file_changed(self, client, connection_id, entry, data):
        self.guake.load_custom_commands()

    def show_resizer_toggled(self, client, connection_id, entry, data):
        """If the gconf var show_resizer be changed, this method will
        be called and will show/hide the resizer.
        """
        if entry.value.get_bool():
            self.guake.resizer.show()
        else:
            self.guake.resizer.hide()

    def trayicon_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_trayicon be changed, this method will
        be called and will show/hide the trayicon.
        """
        if hasattr(self.guake.tray_icon, 'set_status'):
            self.guake.tray_icon.set_status(entry.value.get_bool())
        else:
            self.guake.tray_icon.set_visible(entry.value.get_bool())

    def ontop_toggled(self, client, connection_id, entry, data):
        """If the gconf var window_ontop be changed, this method will
        be called and will set the keep_above attribute in guake's
        main window.
        """
        self.guake.window.set_keep_above(entry.value.get_bool())

    def tab_ontop_toggled(self, client, connection_id, entry, data):
        """ tab_ontop changed
        """
        self.guake.set_tab_position()

    def tabbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_tabbar be changed, this method will be
        called and will show/hide the tabbar.
        """
        if entry.value.get_bool():
            self.guake.toolbar.show()
        else:
            self.guake.toolbar.hide()

    def alignment_changed(self, client, connection_id, entry, data):
        """If the gconf var window_halignment be changed, this method will
        be called and will call the move function in guake.
        """
        self.guake.set_final_window_rect()
        self.guake.set_tab_position()
        self.guake.force_move_if_shown()

    def size_changed(self, client, connection_id, entry, data):
        """If the gconf var window_height or window_width are changed,
        this method will be called and will call the resize function
        in guake.
        """
        self.guake.set_final_window_rect()

    def cursor_blink_mode_changed(self, client, connection_id, entry, data):
        """Called when cursor blink mode settings has been changed
        """
        for term in self.guake.notebook.iter_terminals():
            term.set_property("cursor-blink-mode", entry.value.get_int())

    def cursor_shape_changed(self, client, connection_id, entry, data):
        """Called when the cursor shape settings has been changed
        """
        for term in self.guake.notebook.iter_terminals():
            term.set_property("cursor-shape", entry.value.get_int())

    def scrollbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_scrollbar be changed, this method will
        be called and will show/hide scrollbars of all terminals open.
        """
        for term in self.guake.notebook.iter_terminals():
            # There is an hbox in each tab of the main notebook and it
            # contains a Terminal and a Scrollbar. Since only have the
            # Terminal here, we're going to use this to get the
            # scrollbar and hide/show it.
            hbox = term.get_parent()
            terminal, scrollbar = hbox.get_children()
            if entry.value.get_bool():
                scrollbar.show()
            else:
                scrollbar.hide()

    def history_size_changed(self, client, connection_id, entry, data):
        """If the gconf var history_size be changed, this method will
        be called and will set the scrollback_lines property of all
        terminals open.
        """
        for i in self.guake.notebook.iter_terminals():
            i.set_scrollback_lines(entry.value.get_int())

    def keystroke_output(self, client, connection_id, entry, data):
        """If the gconf var scroll_output be changed, this method will
        be called and will set the scroll_on_output in all terminals
        open.
        """
        for i in self.guake.notebook.iter_terminals():
            i.set_scroll_on_output(entry.value.get_bool())

    def keystroke_toggled(self, client, connection_id, entry, data):
        """If the gconf var scroll_keystroke be changed, this method
        will be called and will set the scroll_on_keystroke in all
        terminals open.
        """
        for i in self.guake.notebook.iter_terminals():
            i.set_scroll_on_keystroke(entry.value.get_bool())

    def default_font_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_default_font be changed, this method
        will be called and will change the font style to the gnome
        default or to the chosen font in style/font/style in all
        terminals open.
        """
        font_name = None
        if entry.value.get_bool():
            # cannot directly use the Gio API since it requires to rework completely
            # the library inclusion, remove dependencies on gobject and so on.
            # Instead, issuing a direct command line request
            proc = subprocess.Popen(['gsettings', 'get', DCONF_MONOSPACE_FONT_PATH,
                                     DCONF_MONOSPACE_FONT_KEY], stdout=subprocess.PIPE)
            font_name = proc.stdout.readline().replace("'", "")
            if font_name is None:
                # Back to gconf
                font_name = client.get_string(GCONF_MONOSPACE_FONT_PATH)
            proc.kill()
        else:
            key = KEY('/style/font/style')
            font_name = client.get_string(key)

        if not font_name:
            log.error("Error: unable to find font name !!!")
            return
        font = FontDescription(font_name)
        if not font:
            return
        for i in self.guake.notebook.iter_terminals():
            i.set_font(font)

    def allow_bold_toggled(self, client, connection_id, entry, data):
        """If the gconf var allow_bold is changed, this method will be called
        and will change the VTE terminal o.
        displaying characters in bold font.
        """
        for term in self.guake.notebook.iter_terminals():
            term.set_allow_bold(entry.value.get_bool())

    def palette_font_and_background_color_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_palette_font_and_background_color be changed, this method
        will be called and will change the font color and the background color to the color
        defined in the palette.
        """
        pass

    def fstyle_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/style be changed, this method
        will be called and will change the font style in all terminals
        open.
        """
        font = FontDescription(entry.value.get_string())
        for i in self.guake.notebook.iter_terminals():
            i.set_font(font)

    def fcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/color be changed, this method
        will be called and will change the font color in all terminals
        open.
        """
        fgcolor = gtk.gdk.color_parse(entry.value.get_string())
        use_palette_font_and_background_color = client.get_bool(
            KEY('/general/use_palette_font_and_background_color'))
        if use_palette_font_and_background_color:
            return
        for i in self.guake.notebook.iter_terminals():
            i.set_color_dim(i.custom_fgcolor or fgcolor)
            i.set_color_foreground(i.custom_fgcolor or fgcolor)
            i.set_color_bold(i.custom_fgcolor or fgcolor)

    def fpalette_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/palette be changed, this method
        will be called and will change the color scheme in all terminals
        open.
        """
        fgcolor = gtk.gdk.color_parse(
            client.get_string(KEY('/style/font/color')))
        bgcolor = gtk.gdk.color_parse(
            client.get_string(KEY('/style/background/color')))
        palette = [gtk.gdk.color_parse(color) for color in
                   entry.value.get_string().split(':')]

        use_palette_font_and_background_color = client.get_bool(
            KEY('/general/use_palette_font_and_background_color'))
        if use_palette_font_and_background_color and len(palette) > 16:
            fgcolor = palette[16]
            bgcolor = palette[17]
        for i in self.guake.notebook.iter_terminals():
            i.set_color_dim(fgcolor)
            i.set_color_foreground(fgcolor)
            i.set_color_bold(fgcolor)
            i.set_color_background(bgcolor)
            i.set_background_tint_color(bgcolor)
        for i in self.guake.notebook.iter_terminals():
            i.set_colors(fgcolor, bgcolor, palette[:16])

    def bgcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/color be changed, this
        method will be called and will change the background color in
        all terminals open.
        """
        use_palette_font_and_background_color = client.get_bool(
            KEY('/general/use_palette_font_and_background_color'))
        if use_palette_font_and_background_color:
            log.debug("do not set background from user")
            return
        bgcolor = gtk.gdk.color_parse(entry.value.get_string())
        for i in self.guake.notebook.iter_terminals():
            i.set_color_background(i.custom_bgcolor or bgcolor)
            i.set_background_tint_color(i.custom_bgcolor or bgcolor)

    def bgimage_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/image be changed, this
        method will be called and will change the background image and
        will set the transparent flag to false if an image is set in
        all terminals open.
        """
        self.guake.set_background_image(entry.value.get_string())

    def bgtransparency_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/transparency be changed, this
        method will be called and will set the saturation and transparency
        properties in all terminals open.
        """
        self.guake.set_background_transparency(entry.value.get_int())

    def backspace_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_backspace be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.notebook.iter_terminals():
            i.set_backspace_binding(entry.value.get_string())

    def delete_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_delete be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.notebook.iter_terminals():
            i.set_delete_binding(entry.value.get_string())

    def max_tab_name_length_changed(self, client, connection_id, entry, data):
        """If the gconf var max_tab_name_length be changed, this method will
        be called and will set the tab name length limit.
        """

        # avoid get window title before terminal is ready
        if self.guake.notebook.get_current_terminal().get_window_title() is None:
            return

        self.guake.recompute_tabs_titles()

    def abbreviate_tab_names_changed(self, client, connection_id, entry, data):
        """If the gconf var abbreviate_tab_names be changed, this method will
        be called and will update tab names.
        """
        abbreviate_tab_names = client.get_bool(KEY('/general/abbreviate_tab_names'))
        self.guake.abbreviate = abbreviate_tab_names and self.guake.is_tabs_scrollbar_visible()
        self.guake.recompute_tabs_titles()


class GConfKeyHandler(object):

    """Handles changes in keyboard shortcuts.
    """

    def __init__(self, guake):
        """Constructor of Keyboard, only receives the guake instance
        to be used in internal methods.
        """
        self.guake = guake
        self.accel_group = None  # see reload_accelerators
        self.client = gconf.client_get_default()

        notify_add = self.client.notify_add

        # Setup global keys
        self.globalhotkeys = {}
        globalkeys = ['show_hide']
        for key in globalkeys:
            notify_add(GKEY(key), self.reload_global)
            self.client.notify(GKEY(key))

        # Setup local keys
        keys = ['toggle_fullscreen', 'new_tab', 'close_tab', 'rename_current_tab',
                'previous_tab', 'next_tab', 'clipboard_copy', 'clipboard_paste',
                'quit', 'zoom_in', 'zoom_out', 'increase_height', 'decrease_height',
                'increase_transparency', 'decrease_transparency', 'toggle_transparency',
                "search_on_web", 'move_tab_left', 'move_tab_right',
                'switch_tab1', 'switch_tab2', 'switch_tab3', 'switch_tab4', 'switch_tab5',
                'switch_tab6', 'switch_tab7', 'switch_tab8', 'switch_tab9', 'switch_tab10',
                'switch_tab_last', 'reset_terminal']
        for key in keys:
            notify_add(LKEY(key), self.reload_accelerators)
            self.client.notify(LKEY(key))

    def reload_global(self, client, connection_id, entry, data):
        """Unbind all global hotkeys and rebind the show_hide
        method. If more global hotkeys should be added, just connect
        the gconf key to the watch system and add.
        """
        gkey = entry.get_key()
        key = entry.get_value().get_string()

        if key == 'disabled':
            return

        try:
            self.guake.hotkeys.unbind(self.globalhotkeys[gkey])
        except KeyError:
            pass
        self.globalhotkeys[gkey] = key
        if not self.guake.hotkeys.bind(key, self.guake.show_hide):
            keyval, mask = gtk.accelerator_parse(key)
            label = gtk.accelerator_get_label(keyval, mask)
            filename = pixmapfile('guake-notification.png')
            guake.notifier.show_message(
                _('Guake Terminal'),
                _('A problem happened when binding <b>%s</b> key.\n'
                  'Please use Guake Preferences dialog to choose another '
                  'key') % xml_escape(label), filename)

    def reload_accelerators(self, *args):
        """Reassign an accel_group to guake main window and guake
        context menu and calls the load_accelerators method.
        """
        if self.accel_group:
            self.guake.window.remove_accel_group(self.accel_group)
        self.accel_group = gtk.AccelGroup()
        self.guake.window.add_accel_group(self.accel_group)
        self.guake.context_menu.set_accel_group(self.accel_group)
        self.load_accelerators()

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the main accel_group.
        """
        gets = lambda x: self.client.get_string(LKEY(x))
        key, mask = gtk.accelerator_parse(gets('reset_terminal'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_reset_terminal)

        key, mask = gtk.accelerator_parse(gets('quit'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_quit)

        key, mask = gtk.accelerator_parse(gets('new_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_add)

        key, mask = gtk.accelerator_parse(gets('close_tab'))
        if key > 0:
            self.accel_group.connect_group(
                key, mask, gtk.ACCEL_VISIBLE,
                self.guake.close_tab)

        key, mask = gtk.accelerator_parse(gets('previous_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_prev)

        key, mask = gtk.accelerator_parse(gets('next_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_next)

        key, mask = gtk.accelerator_parse(gets('move_tab_left'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_move_tab_left)

        key, mask = gtk.accelerator_parse(gets('move_tab_right'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_move_tab_right)

        key, mask = gtk.accelerator_parse(gets('rename_current_tab'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_rename_current_tab)

        key, mask = gtk.accelerator_parse(gets('clipboard_copy'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_copy_clipboard)

        key, mask = gtk.accelerator_parse(gets('clipboard_paste'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_paste_clipboard)

        key, mask = gtk.accelerator_parse(gets('toggle_fullscreen'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_toggle_fullscreen)

        key, mask = gtk.accelerator_parse(gets('toggle_hide_on_lose_focus'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_toggle_hide_on_lose_focus)

        key, mask = gtk.accelerator_parse(gets('zoom_in'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_in)

        key, mask = gtk.accelerator_parse(gets('zoom_in_alt'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_in)

        key, mask = gtk.accelerator_parse(gets('zoom_out'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_zoom_out)

        key, mask = gtk.accelerator_parse(gets('increase_height'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_increase_height)

        key, mask = gtk.accelerator_parse(gets('decrease_height'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_decrease_height)

        key, mask = gtk.accelerator_parse(gets('increase_transparency'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_increase_transparency)

        key, mask = gtk.accelerator_parse(gets('decrease_transparency'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_decrease_transparency)

        key, mask = gtk.accelerator_parse(gets('toggle_transparency'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_toggle_transparency)

        for tab in xrange(1, 11):
            key, mask = gtk.accelerator_parse(gets('switch_tab%d' % tab))
            if key > 0:
                self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                               self.guake.gen_accel_switch_tabN(tab - 1))

        key, mask = gtk.accelerator_parse(gets('switch_tab_last'))
        if key > 0:
            self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                           self.guake.accel_switch_tab_last)

        try:
            key, mask = gtk.accelerator_parse(gets('search_on_web'))
            if key > 0:
                self.accel_group.connect_group(key, mask, gtk.ACCEL_VISIBLE,
                                               self.guake.search_on_web)
        except Exception:
            log.exception("Exception occured")
