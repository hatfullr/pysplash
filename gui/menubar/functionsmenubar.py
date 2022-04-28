from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk


class FunctionsMenuBar(tk.Menu, object):
    def __init__(self, master, gui, *args, name='functions', tearoff=0, **kwargs):
        super(FunctionsMenuBar, self).__init__(
            master,
            *args,
            name=name,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(label='Make rotation movie', command=gui.make_rotation_movie)
        
