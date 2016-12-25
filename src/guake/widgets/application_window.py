import logging
from guake import gi
from gi.repository import Gtk
from gi.repository import Gdk
from guake.widgets import GuakeWidget
logger = logging.getLogger(__name__)

class GuakeApplicationWindow(GuakeWidget, Gtk.ApplicationWindow):

    __filename__ = "app.ui"

    def __init__(self, *args, **kwargs):
        app = kwargs.get("application")
        if app is not None:
            self.set_application(app)
        self._set_window_position()
        self._set_window_size()
        self.visible = kwargs.get("visible", False)

    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, value):
        self._visible = value
        if value:
            self.show_all()
            self.present()
            return
        self.hide()
        return

    def _select_screen(self):
        # TODO: get tagret screen from settings
        return Gdk.Screen.get_default()

    def _get_screen_size(self):
        screen = self._select_screen()
        return (screen.get_width(), screen.get_height())

    def _set_window_size(self):
        """
            - get window height from the settings
            - set window width as screen width
            - set window height

        """
        # TODO: read height_setting from settings
        height_rate = 0.7
        screen_width, screen_height = self._get_screen_size()
        self.set_default_size(screen_width, screen_height * height_rate)

    def _set_window_position(self):
        # TODO: get window position from settings
        self.move(0, 0)

    # handlers
    def show_hide_handler(self, *args):
        self.visible = not self.visible
        return
