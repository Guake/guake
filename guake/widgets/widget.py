import os
from guake import gi
from gi.repository import Gtk
from gi.repository import Gdk


class GuakeWidget(object):

    # __filename__ should be set in a child class
    __filename__ = None

    def __new__(cls, *args, **kwargs):
        """Create application from glade .ui file;
        ApplicationWindow identifier in the ui-file should be equal to cls.__name__"""
        assert isinstance(cls.__filename__, str), "%s has invalid __filename__!" % cls
        datapath = kwargs.get("datapath", "./data")
        filename = os.path.join(datapath, "ui", cls.__filename__)
        builder = Gtk.Builder()
        builder.add_from_file(filename)
        instance = builder.get_object(cls.__name__)
        assert instance is not None, "Gtk widget %s not found!" % cls.__name__
        instance.__class__ = cls
        del(builder)
        return instance
