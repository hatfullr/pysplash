import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from functions.getallchildren import get_all_children
import globals
import numpy as np
from hotkeyslist import hotkeyslist

# This class binds buttons to the gui widget

class Hotkeys(object):
    def __init__(self, root):
        if globals.debug > 1: print("hotkeys.__init__")
        self.root = root
        self.registry = {}

    def bind(self, name, commands):
        if globals.debug > 1: print("hotkeys.add")
        if name not in hotkeyslist.keys():
            raise KeyError("Invalid hotkey name '"+name+"'. It is only possible to bind hotkeys using a name that appears as a key the hotkeyslist dictionary.")

        if not isinstance(commands, (list, tuple, np.ndarray)):
            commands = [commands]

        def command(*args, **kwargs):
            for c in commands: c(*args, **kwargs)
        self.registry[name] = [[key, self.root.bind(key, command, add="+")] for key in hotkeyslist[name]]

    def unbind(self, name):
        if globals.debug > 1: print("hotkeys.remove")
        if name in self.registry.keys():
            for key, bid in self.registry[name]:
                self.root.unbind(key, bid)
            del self.registry[name]
        else:
            raise KeyError("No key '"+name+"' found in the hotkey registry. Please make sure a binding has been created for this name before trying to unbind it.")
        

