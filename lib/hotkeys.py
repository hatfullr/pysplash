import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk
import globals
import numpy as np
from hotkeyslist import hotkeyslist
from functions.getallchildren import get_all_children

# This class binds buttons to the gui widget

class Hotkeys(object):
    def __init__(self, root):
        if globals.debug > 1: print("hotkeys.__init__")
        self.root = root.winfo_toplevel()
        self.registry = {}

        # Bind all the modifiers so that we know when they are pressed/released
        self.root.bind("<KeyPress>", self.on_keypress,add="+")
        self.root.bind("<KeyRelease>", self.on_keyrelease,add="+")
        self.root.bind("<FocusOut>", self.on_focusout, add="+")
        self.modifiers = {
            '<Control>' : False,
            '<Shift>': False,
            '<Alt>' : False,
        }

    def bind(self, name, commands):
        if globals.debug > 1: print("hotkeys.bind")
        if name not in hotkeyslist.keys():
            raise KeyError("Invalid hotkey name '"+name+"'. It is only possible to bind hotkeys using a name that appears as a key the hotkeyslist dictionary.")

        if not isinstance(commands, (list, tuple, np.ndarray)):
            commands = [commands]

        if self.is_bound(name):
            raise KeyError("The hotkey action '"+name+"' is already bound")
        
        for key in hotkeyslist[name]["keylist"]:

            if "<Shift>" in hotkeyslist[name]["modifiers"] or "Shift" in hotkeyslist[name]["modifiers"]:
                if len(key) == 3:
                    if key[0] == "<" and key[2] == ">":
                        key = "<"+key[1].upper()+">"
                elif len(key) == 1: key = key.upper()
            
            if hotkeyslist[name]["type"] == "global":
                self.bind_global(name, key, lambda event: self.command(name,commands,event))
            elif hotkeyslist[name]["type"] == "local":
                self.bind_local(name, key, lambda event: self.command(name,commands,event))
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
                self.registry[name].append([child, key, child.bind(key, command)])

    def on_keypress(self, event):
        if "Control" in event.keysym: key = "<Control>"
        elif "Shift" in event.keysym: key = "<Shift>"
        elif "Alt" in event.keysym: key = "<Alt>"
        else: return
        self.modifiers[key] = True

    def on_keyrelease(self, event):
        if "Control" in event.keysym: key = "<Control>"
        elif "Shift" in event.keysym: key = "<Shift>"
        elif "Alt" in event.keysym: key = "<Alt>"
        else: return
        self.modifiers[key] = False

    def on_focusout(self, event):
        for key in self.modifiers.keys(): self.modifiers[key] = False

    def command(self, name, commands, event):
        pressed_modifiers = [key for key in self.modifiers.keys() if self.modifiers[key]]
        if hotkeyslist[name]['modifiers'] == []:
            if pressed_modifiers == []:
                globals.hotkey_pressed = True
                for c in commands:
                    try:
                        c(event)
                    except:
                        raise
                        break
                globals.hotkey_pressed = False
        else:
            for modifier in hotkeyslist[name]['modifiers']:
                if modifier not in pressed_modifiers: return
            globals.hotkey_pressed = True
            for c in commands:
                try:
                    c(event)
                except:
                    raise
                    break
            globals.hotkey_pressed = False

    # Check if a particular method has any set bindings
    def is_bound(self, name):
        return name in self.registry
