import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk
from functions.getallchildren import get_all_children
import globals
import numpy as np
from hotkeyslist import hotkeyslist
from functions.getallchildren import get_all_children

# This class binds buttons to the gui widget

class Hotkeys(object):
    def __init__(self, root):
        if globals.debug > 1: print("hotkeys.__init__")
        self.root = root
        self.registry = {}

    def bind(self, name, commands):
        if globals.debug > 1: print("hotkeys.bind")
        if name not in hotkeyslist.keys():
            raise KeyError("Invalid hotkey name '"+name+"'. It is only possible to bind hotkeys using a name that appears as a key the hotkeyslist dictionary.")

        if not isinstance(commands, (list, tuple, np.ndarray)):
            commands = [commands]

        def command(*args, **kwargs):
            for c in commands: c(*args, **kwargs)
            
        if name in self.registry:
            raise KeyError("The hotkey action '"+name+"' is already bound")
        
        for key in hotkeyslist[name]["keylist"]:
            if hotkeyslist[name]["type"] == "global":
                self.bind_global(name, key, command)
            elif hotkeyslist[name]["type"] == "local":
                self.bind_local(name, key, command)
            else:
                raise ValueError("Hotkey '"+name+"' has type '"+hotkeyslist[name]["type"]+"', but must be 'global' or 'local'")

    def unbind(self, name, throwerror=True):
        if globals.debug > 1: print("hotkeys.unbind")
        if name in self.registry.keys():
            for widget, key, bid in self.registry[name]:
                widget.unbind(key, bid)
            del self.registry[name]
        elif throwerror:
            raise KeyError("No key '"+name+"' found in the hotkey registry. Please make sure a binding has been created for this name before trying to unbind it.")
        
    def bind_global(self, name, key, command):
        if globals.debug > 1: print("hotkeys.bind_global")
        if name not in self.registry.keys(): self.registry[name] = []
        self.registry[name].append([self.root, key, self.root.bind(key, command, add="+")])
    
    def bind_local(self, name, key, command):
        if globals.debug > 1: print("hotkeys.bind_local")
        # This hotkey needs to work only when the root widget has focus... (?)
        if name not in self.registry.keys(): self.registry[name] = []
        for child in get_all_children(self.root):
            if not isinstance(child, (tk.Entry, ttk.Entry, ttk.Combobox)):
                self.registry[name].append([child, key, child.bind(key, command, add="+")])

