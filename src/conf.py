"""
Copyright (C) 2011  Lincoln de Sousa <lincoln@guake.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

from gi.repository import GConf
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango

from guake.globals import KEY, GCONF_PATH
from guake.prefs import PrefsDialog, LKEY, GKEY
from guake.common import ERASE_BINDINGS_ENUM

GNOME_FONT_PATH = '/desktop/gnome/interface/monospace_font_name'

class GConfHandler(object):
    """Handles gconf changes, if any gconf variable is changed, a
    different method is called to handle this change.
    """
    def __init__(self, guake):
        """Constructor of GConfHandler, just add the guake dir to the
        gconf client and bind the keys to its handler methods.
        """
        self.guake = guake

        client = GConf.Client.get_default()
        client.add_dir(GCONF_PATH, GConf.ClientPreloadType.PRELOAD_RECURSIVE)

        notify_add = lambda x, y: client.notify_add(x, y, None)

        # these keys does not need to be watched.
        #notify_add(KEY('/general/default_shell'), self.shell_changed)
        #notify_add(KEY('/general/use_login_shell'), self.login_shell_toggled)
        #notify_add(KEY('/general/use_popup'), self.popup_toggled)
        #notify_add(KEY('/general/window_losefocus'), self.losefocus_toggled)

        notify_add(KEY('/general/show_resizer'), self.show_resizer_toggled)

        notify_add(KEY('/general/use_trayicon'), self.trayicon_toggled)
        notify_add(KEY('/general/window_ontop'), self.ontop_toggled)
        # notify_add(KEY('/general/window_tabbar'), self.tabbar_toggled)
        notify_add(KEY('/general/window_height'), self.size_changed)

        notify_add(KEY('/general/use_scrollbar'), self.scrollbar_toggled)
        notify_add(KEY('/general/history_size'), self.history_size_changed)
        notify_add(KEY('/general/scroll_output'), self.keystroke_output)
        notify_add(KEY('/general/scroll_keystroke'), self.keystroke_toggled)

        notify_add(KEY('/general/use_default_font'), self.default_font_toggled)
        notify_add(KEY('/style/font/style'), self.fstyle_changed)
        notify_add(KEY('/style/font/color'), self.fcolor_changed)
        # FIXME: when fpalette_changes is executed on Gtk 3, vte displays
        # all colors as black
        #notify_add(KEY('/style/font/palette'), self.fpalette_changed)
        notify_add(KEY('/style/background/color'), self.bgcolor_changed)
        notify_add(KEY('/style/background/image'), self.bgimage_changed)
        notify_add(KEY('/style/background/transparency'),
                   self.bgtransparency_changed)

        notify_add(KEY('/general/compat_backspace'), self.backspace_changed)
        notify_add(KEY('/general/compat_delete'), self.delete_changed)

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
        self.guake.tray_icon.set_visible(entry.value.get_bool())

    def ontop_toggled(self, client, connection_id, entry, data):
        """If the gconf var window_ontop be changed, this method will
        be called and will set the keep_above attribute in guake's
        main window.
        """
        self.guake.window.set_keep_above(entry.value.get_bool())

    # def tabbar_toggled(self, client, connection_id, entry, data):
    #     """If the gconf var use_tabbar be changed, this method will be
    #     called and will show/hide the tabbar.
    #     """
    #     if entry.value.get_bool():
    #         self.guake.toolbar.show()
    #     else:
    #         self.guake.toolbar.hide()

    def alignment_changed(self, client, connection_id, entry, data):
        """If the gconf var window_halignment be changed, this method will
        be called and will call the move function in guake.
        """
        window_rect = self.guake.get_final_window_rect()
        self.guake.window.move(window_rect.x, window_rect.y)

    def size_changed(self, client, connection_id, entry, data):
        """If the gconf var window_height or window_width are changed,
        this method will be called and will call the resize function
        in guake.
        """
        x, y, width, height = self.guake.get_final_window_rect()
        self.guake.window.move(x, y)
        self.guake.window.resize(width, height)

    def scrollbar_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_scrollbar be changed, this method will
        be called and will show/hide scrollbars of all terminals open.
        """
        for i in self.guake.term_list:
            # There is an hbox in each tab of the main notebook and it
            # contains a Terminal and a Scrollbar. Since only have the
            # Terminal here, we're going to use this to get the
            # scrollbar and hide/show it.
            hbox = i.get_parent()
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
        for i in self.guake.term_list:
            i.set_scrollback_lines(entry.value.get_int())

    def keystroke_output(self, client, connection_id, entry, data):
        """If the gconf var scroll_output be changed, this method will
        be called and will set the scroll_on_output in all terminals
        open.
        """
        for i in self.guake.term_list:
            i.set_scroll_on_output(entry.value.get_bool())

    def keystroke_toggled(self, client, connection_id, entry, data):
        """If the gconf var scroll_keystroke be changed, this method
        will be called and will set the scroll_on_keystroke in all
        terminals open.
        """
        for i in self.guake.term_list:
            i.set_scroll_on_keystroke(entry.value.get_bool())

    def default_font_toggled(self, client, connection_id, entry, data):
        """If the gconf var use_default_font be changed, this method
        will be called and will change the font style to the gnome
        default or to the choosen font in style/font/style in all
        terminals open.
        """
        if entry.value.get_bool():
            key = GNOME_FONT_PATH
        else:
            key = KEY('/style/font/style')

        font = Pango.font_description_from_string(client.get_string(key))
        for i in self.guake.term_list:
            i.set_font(font)

    def fstyle_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/style be changed, this method
        will be called and will change the font style in all terminals
        open.
        """
        font = Pango.font_description_from_string(entry.value.get_string())
        for i in self.guake.term_list:
            i.set_font(font)

    def fcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/color be changed, this method
        will be called and will change the font color in all terminals
        open.
        """
        success, fgcolor = Gdk.color_parse(entry.value.get_string())
        if not success:
            warnings.warn('Unable to parse color %s' % fgcolor)
            return

        for i in self.guake.term_list:
            i.set_color_dim(fgcolor)
            i.set_color_foreground(fgcolor)
            i.set_color_bold(fgcolor)

    def fpalette_changed(self, client, connection_id, entry, data):
        """If the gconf var style/font/palette be changed, this method
        will be called and will change the color scheme in all terminals
        open.
        """
        success, fgcolor = Gdk.color_parse(
            client.get_string(KEY('/style/font/color')))
        if not success:
            warnings.warn('Unable to parse color %s' % client.get_string(KEY('/style/font/color')))
            return

        success, bgcolor = Gdk.color_parse(
            client.get_string(KEY('/style/background/color')))
        if not success:
            warnings.warn('Unable to parse color %s' % client.get_string(KEY('/style/background/color')))
            return

        palette = []
        for color in entry.value.get_string().split(':'):
            success, pcolor = Gdk.color_parse(color)
            if not success:
                warnings.warn('Unable to parse color %s' % color)
                return
            palette.append(pcolor)

        for i in self.guake.term_list:
            i.set_colors(fgcolor, bgcolor, palette)

    def bgcolor_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/color be changed, this
        method will be called and will change the background color in
        all terminals open.
        """
        success, bgcolor = Gdk.color_parse(entry.value.get_string())
        if not success:
            warnings.warn('Unable to parse color %s' % entry.value.get_string())
            return

        for i in self.guake.term_list:
            i.set_color_background(bgcolor)
            i.set_background_tint_color(bgcolor)

    def bgimage_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/image be changed, this
        method will be called and will change the background image and
        will set the transparent flag to false if an image is set in
        all terminals open.
        """
        image = entry.value.get_string()
        for i in self.guake.term_list:
            if image and os.path.exists(image):
                i.set_background_image_file(image)
                i.set_background_transparent(False)
            else:
                """We need to clear the image if it's not set but there is
                a bug in vte python bidnings which doesn't allow None to be
                passed to set_background_image (C GTK function expects NULL).
                The user will need to restart Guake after clearing the image.
                i.set_background_image(None)
                """
                if self.guake.has_argb:
                    i.set_background_transparent(False)
                else:
                    i.set_background_transparent(True)

    def bgtransparency_changed(self, client, connection_id, entry, data):
        """If the gconf var style/background/transparency be changed, this
        method will be called and will set the saturation and transparency
        properties in all terminals open.
        """
        transparency = entry.value.get_int()
        for i in self.guake.term_list:
            i.set_background_saturation(transparency / 100.0)
            if self.guake.has_argb:
                i.set_opacity(int((100 - transparency) / 100.0 * 65535))

    def backspace_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_backspace be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.term_list:
            i.set_backspace_binding(ERASE_BINDINGS_ENUM[entry.value.get_string()])

    def delete_changed(self, client, connection_id, entry, data):
        """If the gconf var compat_delete be changed, this method
        will be called and will change the binding configuration in
        all terminals open.
        """
        for i in self.guake.term_list:
            i.set_delete_binding(ERASE_BINDINGS_ENUM[entry.value.get_string()])


class GConfKeyHandler(object):
    """Handles changes in keyboard shortcuts.
    """
    def __init__(self, guake):
        """Constructor of Keyboard, only receives the guake instance
        to be used in internal methods.
        """
        self.guake = guake
        self.accel_group = None # see reload_accelerators
        self.client = GConf.Client.get_default()

        notify_add = lambda x, y: self.client.notify_add(x, y, None)
        notify_add(GKEY('show_hide'), self.reload_globals)

        keys = ['toggle_fullscreen', 'new_tab', 'close_tab', 'rename_tab',
                'previous_tab', 'next_tab', 'clipboard_copy', 'clipboard_paste',
                'quit',
                ]
        for key in keys:
            notify_add(LKEY(key), self.reload_accelerators)

        self.reload_accelerators()

    def reload_globals(self, client, connection_id, entry, data):
        """Unbind all global hotkeys and rebind the show_hide
        method. If more global hotkeys should be added, just connect
        the gconf key to the watch system and add.
        """
        self.guake.hotkeys.unbind_all()
        key = entry.get_value().get_string()
        if not self.guake.hotkeys.bind(key, self.guake.show_hide):
            raise ShowableError(_('key binding error'),
                                _('Unable to bind global <b>%s</b> key') % key,
                                -1)

    def reload_accelerators(self, *args):
        """Reassign an accel_group to guake main window and guake
        context menu and calls the load_accelerators method.
        """
        if self.accel_group:
            self.guake.window.remove_accel_group(self.accel_group)
        self.accel_group = Gtk.AccelGroup()
        self.guake.window.add_accel_group(self.accel_group)
        self.guake.context_menu.set_accel_group(self.accel_group)
        self.load_accelerators()

    def load_accelerators(self):
        """Reads all gconf paths under /apps/guake/keybindings/local
        and adds to the main accel_group.
        """
        accel_handler = {
            'quit' : self.guake.accel_quit,
            'new_tab' : self.guake.accel_add,
            'close_tab' : self.guake.close_tab,
            'previous_tab' : self.guake.accel_prev,
            'next_tab' : self.guake.accel_next,
            'rename_tab' : self.guake.accel_rename,
            'clipboard_copy' : self.guake.accel_copy_clipboard,
            'clipboard_paste' : self.guake.accel_paste_clipboard,
            'toggle_fullscreen' : self.guake.accel_toggle_fullscreen
        }

        for accel, handler in accel_handler.iteritems():
            key, mask = Gtk.accelerator_parse(self.client.get_string(LKEY(accel)))
            if key > 0:
                self.accel_group.connect(key, mask, Gtk.AccelFlags.VISIBLE,
                                         handler)
