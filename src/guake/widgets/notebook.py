import logging
from guake import gi
from gi.repository import Gtk
from gi.repository import Gdk

logger = logging.getLogger(__name__)


class GuakeNotebook(Gtk.Notebook):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_tab_pos(Gtk.PositionType.BOTTOM)
