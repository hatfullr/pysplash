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
        bind = kwargs.pop('bind',True)

        if hotkey is not None and command is not None:
            if bind: self.hotkeys.bind(hotkey, command)
            kwargs['accelerator'] = hotkeys_to_string(hotkey).replace("(","").replace(")","")
        
        state = kwargs.get('state','normal')
        kwargs['state'] = state
        
        if kwargs.pop('can_disable', True):
            self.states[label] = {'state':state, 'hotkey':hotkey}
            if state == 'disabled' and hotkey is not None:
                if self.hotkeys.is_bound(hotkey): self.hotkeys.disable(hotkey)

        kwargs['label'] = label
        super(Menu,self).add_command(*args,**kwargs)
        self.index += 1

    def add_checkbutton(self, label, *args, **kwargs):
        hotkey = kwargs.pop('hotkey',None)
        command = kwargs.get('command', None)
        bind = kwargs.pop('bind',True)

        if hotkey is not None and command is not None:
            if bind: self.hotkeys.bind(hotkey, command)
            kwargs['accelerator'] = hotkeys_to_string(hotkey).replace("(","").replace(")","")
        
        state = kwargs.get('state','normal')
        kwargs['state'] = state
        
        if kwargs.pop('can_disable', True):
            self.states[label] = {'state':state, 'hotkey':hotkey}
            if state == 'disabled' and hotkey is not None:
                if self.hotkeys.is_bound(hotkey): self.hotkeys.disable(hotkey)

        kwargs['label'] = label
        super(Menu,self).add_checkbutton(*args,**kwargs)
        self.index += 1

    def insert_separator(self):
        super(Menu,self).insert_separator(self.index)
        self.index += 1

    def set_state(self, state, label=None):
        if label is None:
            for l, s in self.states.items():
                self.states[l]['state'] = state
                self.entryconfig(l,state=state)
                if s['hotkey'] is not None and self.hotkeys.is_bound(s['hotkey']):
                    if state == 'disabled': self.hotkeys.disable(s['hotkey'])
                    elif state == 'normal' : self.hotkeys.enable(s['hotkey'])
        else:
            self.states[label]['state'] = state
            self.entryconfig(label,state=state)
            if self.states[label]['hotkey'] is not None and self.hotkeys.is_bound(s['hotkey']):
                if state == 'disabled': self.hotkeys.disable(self.states[label]['hotkey'])
                elif state == 'normal' : self.hotkeys.enable(self.states[label]['hotkey'])
                

    def disable(self,event=None,label=None):
        self.set_state('disabled',label=label)

    def enable(self,event=None,label=None):
        self.set_state('normal',label=label)
    
