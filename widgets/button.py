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
        
        self._command_cid = None
        if command: self._command_cid = self.bind("<Button-1>", command)

        # Mouse hover behavior
        self.bind("<Enter>", lambda *args,**kwargs: self.state(["active"]))
        self.bind("<Leave>", lambda *args,**kwargs: self.state(["!active"]))

    def configure(self, command=None, *args, **kwargs):
        if command:
            if self._command_cid: self.unbind(self._command_cid)
            self._command_cid = self.bind("<Button-1>", command)
        super(Button, self).configure(*args, **kwargs)
