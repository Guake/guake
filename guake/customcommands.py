import json
import os

import gi
import inspect
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(os.path.expandvars("$HOME/.config/guake/") + "guake.log")
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


def _line_():
    """Returns the current line number in our program."""
    return str(inspect.currentframe().f_back.f_lineno)


def _file_():
    return str(__file__)


class CustomCommands:

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
        file_path = self.settings.general.get_string("custom-command-file")
        return file_path is not None

    def get_file_path(self):
        return os.path.expanduser(self.settings.general.get_string("custom-command-file"))

    def _load_json(self, file_name):
        logger.info("%s:%s  Loading menu json file::: %s", _file_(), _line_(), file_name)
        if not os.path.exists(file_name):
            logger.error("%s:%s  Custom file does not exit: %s", _file_(), _line_(), file_name)
            return None
        try:
            with open(file_name, encoding="utf-8") as f:
                data_file = f.read()
                return json.loads(data_file)
        except Exception as e:
            logger.exception(
                "%s:%s  Invalid custom command file %s. Exception: %s",
                _file_(),
                _line_(),
                file_name,
                str(e),
            )

    def build_menu(self):
        if not self.should_load():
            return None
        menu = Gtk.Menu()
        logger.info(
            "%s:%s  Loading session json file: %s", _file_(), _line_(), self.get_file_path()
        )
        cust_comms = self._load_json(self.get_file_path())
        if not cust_comms:
            return None
        for obj in cust_comms:
            try:
                self._parse_custom_commands(obj, menu)
            except AttributeError:
                logger.error(
                    "%s:%s  Loading session json file: %s", _file_(), _line_(), self.get_file_path()
                )
                logger.error(
                    "%s:%s  _parse_custom_commands parsing type: %s", _file_(), _line_(), type(obj)
                )
                logger.error(
                    "%s:%s  _parse_custom_commands parsing json: %s", _file_(), _line_(), obj
                )
                # AttributeError: 'str' object has no attribute 'get', ignore and move on
        return menu

    def _parse_custom_commands(self, json_object, menu):
        logger.info(
            "%s:%s  _parse_custom_commands parsing type: %s",
            _file_(),
            _line_(),
            type(json_object),
        )
        logger.info(
            "%s:%s  _parse_custom_commands parsing json: %s", _file_(), _line_(), json_object
        )
        if json_object.get("type") == "menu":
            newmenu = Gtk.Menu()
            newmenuitem = Gtk.MenuItem(json_object["description"])
            newmenuitem.set_submenu(newmenu)
            newmenuitem.show()
            menu.append(newmenuitem)
            for item in json_object["items"]:
                self._parse_custom_commands(item, newmenu)
        else:
            menu_item = Gtk.MenuItem(json_object["description"])
            custom_command = ""
            space = ""
            for command in json_object["cmd"]:
                custom_command += space + command
                space = " "
            menu_item.connect("activate", self.on_menu_item_activated, custom_command)
            menu.append(menu_item)
            menu_item.show()

    def on_menu_item_activated(self, item, cmd):
        self.callback.on_command_selected(cmd)
