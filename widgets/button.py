from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

# This widget is a replacement for the standard tk.Button because tk.Button
# does not have a controllable height/width.

class Button(tk.Label, object):
    def __init__(
            self,
            master,
            anchor='c',
            bd=1,
            command=None,
            **kwargs,
    ):
        
        super(Button, self).__init__(
            master,
            anchor=anchor,
            bd=bd,
            **kwargs,
        )
        
        self.command_cid = None
        self._bind_command(command)

    def _bind_command(self, command, *args, **kwargs):
        self.command_cid = self.bind("<Button-1>",command)

    def _unbind_command(self, *args, **kwargs):
        if self.command_cid:
            self.unbind(self.command_cid)
            self.command_cid = None
            
    def configure(self, *args, command=None, **kwargs):
        if command: self._bind_command(command)
        super(Button, self).configure(*args, **kwargs)
