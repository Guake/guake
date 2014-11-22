import gtk

from guake.simplegladeapp import SimpleGladeApp
from guake.common import gladefile
from guake.globals import VERSION
from guake.common import pixmapfile


class AboutDialog(SimpleGladeApp):

    """The About Guake dialog class
    """

    def __init__(self):
        super(AboutDialog, self).__init__(gladefile('about.glade'),
                                          root='aboutdialog')
        dialog = self.get_widget('aboutdialog')

        # images
        ipath = pixmapfile('guake-notification.png')
        img = gtk.gdk.pixbuf_new_from_file(ipath)
        dialog.set_property('logo', img)

        dialog.set_name('Guake!')
        dialog.set_version(VERSION)
