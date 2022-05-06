from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

class Button(ttk.Label, object):
    def __init__(self, master, switch=False, command=None, *args, padding="0 -1 0 0", style='TButton', **kwargs):
        super(Button, self).__init__(master, *args, padding=padding, style=style, **kwargs)

        self.switch = switch
        self.command = command

        # Mouse hover behavior
        self.bind("<Enter>", self.on_enter, add='+')
        self.bind("<Leave>", self.on_leave, add='+')

        # Mouse click behavior
        self.bind("<Button-1>", self.on_button1,add='+')
        self.bind("<ButtonRelease-1>", self.on_buttonrelease1,add='+')

        self._button1pressed = False
        self._mousein = False

    def on_button1(self, *args, **kwargs):
        self._button1pressed = True
        if 'disabled' not in self.state(): self.state(['pressed'])

    def on_buttonrelease1(self, *args, **kwargs):
        self._button1pressed = False
        if 'disabled' not in self.state():
            if self._mousein and self.command is not None: self.command(*args, **kwargs)

            if self.switch and not hasattr(self, 'variable'): raise AttributeError("If a button is a switch, it needs to have the 'variable' attribute")
            
            if self.switch:
                if self.variable.get(): self.state(['pressed'])
                else: self.state(['!pressed'])
            else: self.state(['!pressed'])
            
    def on_enter(self, *args, **kwargs):
        self._mousein = True
        if 'disabled' not in self.state():
            self.state(['active','hover'])
            if self._button1pressed: self.state(['pressed','hover'])

    def on_leave(self, *args, **kwargs):
        self._mousein = False
        if 'disabled' not in self.state():
            self.state(['!active','!hover'])
            if self._button1pressed: self.state(['!active','pressed','!hover'])

    def configure(self, *args, **kwargs):
        self.command = kwargs.pop('command',self.command)
        super(Button, self).configure(*args, **kwargs)
