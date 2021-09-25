import builtins

from locale import gettext

builtins.__dict__["_"] = gettext
