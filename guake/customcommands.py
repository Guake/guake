import json
import os

import gi
import logging

from locale import gettext as _
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

log = logging.getLogger(__name__)


class CustomCommands():

    """
    Example for a custom commands file
        [
            {
                "type": "menu",
                "description": "dir listing",
                "items": [
                    {
                        "description": "la",
                        "cmd":["ls", "-la"]
                    },
                    {
                        "description": "tree",
                        "cmd":["tree", ""]
                    }
                ]
            },
            {
                "description": "less ls",
                "cmd": ["ls | less", ""]
            }
        ]
    """

    def __init__(self, settings, callback):
        self.settings = settings
        self.callback = callback

    def should_load(self):
        file_path = self.settings.general.get_string('custom-command-file')
        return file_path is not None

    def get_file_path(self):
        return os.path.expanduser(self.settings.general.get_string('custom-command-file'))

    def _load_json(self, file_name):
        if not os.path.exists(file_name):
            log.error("Custom file does not exit: %s", file_name)
            return None
        try:
            with open(file_name) as f:
                data_file = f.read()
                return json.loads(data_file)
        except Exception as e:
            log.exception("Invalid custom command file %s. Exception: %s", file_name, str(e))

    def build_menu(self):
        if not self.should_load():
            return None
        menu = Gtk.Menu()
        cust_comms = self._load_json(self.get_file_path())
        if not cust_comms:
            return None
        for obj in cust_comms:
            self._parse_custom_commands(obj, menu)
        return menu

    def _parse_custom_commands(self, json_object, menu):
        if json_object.get('type') == "menu":
            newmenu = Gtk.Menu()
            newmenuitem = Gtk.MenuItem(json_object['description'])
            newmenuitem.set_submenu(newmenu)
            newmenuitem.show()
            menu.append(newmenuitem)
            for item in json_object['items']:
                self._parse_custom_commands(item, newmenu)
        else:
            menu_item = Gtk.MenuItem(json_object['description'])
            custom_command = ""
            space = ""
            for command in json_object['cmd']:
                custom_command += (space + command)
                space = " "
            menu_item.connect("activate", self.on_menu_item_activated, custom_command)
            menu.append(menu_item)
            menu_item.show()

    def on_menu_item_activated(self, item, cmd):
        self.callback.on_command_selected(cmd)
