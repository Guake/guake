import logging
from guake import gi
from gi.repository import Gtk
from gi.repository import Gdk
from guake.widgets.widget import GuakeWidget

logger = logging.getLogger(__name__)


class GuakeNotebook(GuakeWidget, Gtk.Notebook):

    __filename__ = "app.ui"


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_all()
