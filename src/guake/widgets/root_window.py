from guake import gi
from guake.widgets.mixin import WidgetMixin
from gi.repository import Gtk
from gi.repository import Gdk


class RootWindowMixin(WidgetMixin):

    def _get_screen(self):
        # TODO: get tagret screen from settings
        return Gdk.Screen.get_default()

    def _get_screen_size(self):
        screen = self._get_screen()
        return (screen.get_width(), screen.get_height())

    def prepare_to_draw(self):
        self._set_window_position()
        self._set_window_size()
        return

    def _set_window_size(self):
        """
            - get window height from the settings
            - set window width as screen width
            - set window height

        """
        # TODO: read height_setting from settings
        height_setting = 0.6
        screen_width, screen_height = self._get_screen_size()
        self.set_default_size(screen_width, screen_height * height_setting)

    def _set_window_position(self):
        self.move(0, 0)


    # handlers
    def on_show_hide(self):
        if self.is_active():
            self.hide()
        else:
            self.show_all()
        return
