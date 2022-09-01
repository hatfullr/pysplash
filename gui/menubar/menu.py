from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from lib.hotkeys import Hotkeys
from hotkeyslist import hotkeyslist
from functions.hotkeystostring import hotkeys_to_string

class Menu(tk.Menu, object):
    def __init__(self,master,root,*args,**kwargs):
        self.states = {}
        super(Menu,self).__init__(master,*args,**kwargs)

        self.hotkeys = Hotkeys(root)
        self.index = 0
        
    def add_command(self,label,*args,**kwargs):
        hotkey = kwargs.pop('hotkey',None)
        command = kwargs.get('command', None)

        if hotkey is not None and command is not None:
            label += " "+hotkeys_to_string(hotkey)
            self.hotkeys.bind(hotkey, command)
        
        kwargs['label'] = label
        
        state = kwargs.get('state','normal')
        kwargs['state'] = state
        
        if kwargs.pop('can_disable', True):
            self.states[label] = {'state':state, 'hotkey':hotkey}
            if state == 'disabled' and hotkey is not None:
                self.hotkeys.disable(hotkey)
        
        super(Menu,self).add_command(*args,**kwargs)
        self.index += 1

    def insert_separator(self):
        super(Menu,self).insert_separator(self.index)
        self.index += 1

    def disable(self,*args,**kwargs):
        for label, s in self.states.items():
            self.states[label]['state'] = 'disabled'
            self.entryconfig(label,state='disabled')
            if s['hotkey'] is not None: self.hotkeys.disable(s['hotkey'])

    def enable(self,*args,**kwargs):
        for label, s in self.states.items():
            self.states[label]['state'] = 'normal'
            self.entryconfig(label,state='normal')
            if s['hotkey'] is not None: self.hotkeys.enable(s['hotkey'])
    
