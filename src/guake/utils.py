from types import MethodType


def attach_methods(Src, dest):
    """Attach methods of class Src to an instance dest"""
    for attr_name in dir(Src):
        if not attr_name.startswith("__"):
            attr = Src.__dict__[attr_name]
            if callable(attr):
                try:
                    dest.__getattribute__(attr_name)
                except AttributeError:
                    dest.__setattr__(attr_name, MethodType(attr, dest))
    return
