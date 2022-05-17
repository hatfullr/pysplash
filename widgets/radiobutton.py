from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from widgets.switchbutton import SwitchButton

class RadioButton(SwitchButton, object):
    def __init__(self, master, value=None, variable=None, *args, **kwargs):
        super(RadioButton,self).__init__(master,*args,**kwargs)
        
        self.value = value
        self.radiovariable = variable
        if not self.radiovariable: self.radiovariable = tk.StringVar()
        if not isinstance(self.radiovariable, tk.StringVar):
            raise TypeError("Keyword argument 'variable' must be of type tk.StringVar. Received '"+type(self.variable).__name__+"'")
        
        def varchange(*args, **kwargs):
            if self.radiovariable.get() != self.value: self.variable.set(False)
        def boolchange(*args, **kwargs):
            if self.variable.get(): self.radiovariable.set(self.value)
        def on_button1(*args, **kwargs):
            if self.variable.get(): return "break"
            else: self.command()
        
        self.variable.trace("w", boolchange)
        self.radiovariable.trace("w", varchange)
        self.bind("<ButtonRelease-1>", on_button1, add='+')

        if self.radiovariable.get() == self.value: self.variable.set(True)
