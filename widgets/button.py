from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

class Button(ttk.Label, object):
    def __init__(self, master, command=None, *args, padding="0 -1 0 0", style='TButton', **kwargs):
        super(Button, self).__init__(master, *args, padding=padding, style=style, **kwargs)

        self.command = command

        # Mouse hover behavior
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

        # Mouse click behavior
        self.bind("<Button-1>", self.on_button1)
        self.bind("<ButtonRelease-1>", self.on_buttonrelease1)

    def on_button1(self, *args, **kwargs):
        if 'disabled' not in self.state():self.state(['pressed'])

    def on_buttonrelease1(self, *args, **kwargs):
        if 'disabled' not in self.state():
            if self.command is not None and 'pressed' in self.state(): self.command(*args, **kwargs)
            self.state(['!pressed'])
            
    def on_enter(self, *args, **kwargs):
        if 'disabled' not in self.state(): self.state(['active'])

    def on_leave(self, *args, **kwargs):
        if 'disabled' not in self.state(): self.state(['!active','!pressed'])

    def configure(self, *args, **kwargs):
        self.command = kwargs.pop('command',self.command)
        super(Button, self).configure(*args, **kwargs)
