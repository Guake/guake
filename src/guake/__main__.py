from __future__ import absolute_import

import gtk

from guake.common import ShowableError
from guake.common import _
from guake.common import test_gconf
from guake.main import main

if __name__ == '__main__':
    if not test_gconf():
        raise ShowableError(_('Guake can not init!'),
                            _('Gconf Error.\n'
                              'Have you installed <b>guake.schemas</b> properly?'))

    if not main():
        gtk.main()
