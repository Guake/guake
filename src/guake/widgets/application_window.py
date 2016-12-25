import os
import logging
from guake import gi
from gi.repository import Gtk
from gi.repository import Gdk

logger = logging.getLogger(__name__)

class GuakeApplicationWindow(Gtk.ApplicationWindow):

    __filename__ = "app.ui"

    def __new__(cls, *args, **kwargs):
        """Create application from glade .ui file; ApplicationWindow identifier 
        in the ui-file should be equal to cls.__name__"""
        _datapath = kwargs.get("datapath", "./data")
        filename = os.path.join(_datapath, "ui", cls.__filename__)
        builder = Gtk.Builder()
        builder.add_from_file(filename)
        instance = builder.get_object(cls.__name__)
        assert instance is not None, "Gtk widget %s not found!" % cls.__name__
        instance.__class__ = cls
        del(builder)
        return instance

    def __init__(self, *args, **kwargs):
        app = kwargs.get("application")
        if app is not None:
            self.set_application(app)
        self._visible = kwargs.get("visible", False)
        self._set_window_position()
        self._set_window_size()

    def _get_screen(self):
        # TODO: get tagret screen from settings
        return Gdk.Screen.get_default()

    def _get_screen_size(self):
        screen = self._get_screen()
        return (screen.get_width(), screen.get_height())

    def _set_window_size(self):
        """
            - get window height from the settings
            - set window width as screen width
            - set window height

        """
        # TODO: read height_setting from settings
        height_rate = 0.6
        screen_width, screen_height = self._get_screen_size()
        self.set_default_size(screen_width, screen_height * height_rate)

    def _set_window_position(self):
        # TODO: get window position from settings
        self.move(0, 0)

    # handlers
    def show_hide_handler(self, *args):
        logger.info(args)
        if self._visible:
            self.hide()
            self._visible = False
            return
        self.show_all()
        self.present()
        self._visible = True
        return
