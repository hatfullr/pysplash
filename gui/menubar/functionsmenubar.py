from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk
from gui.menubar.menu import Menu

class FunctionsMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        super(FunctionsMenuBar, self).__init__(
            master,
            gui.window,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(
            'Make movie',
            command=gui.make_movie,
            state='disabled',
            can_disable=True,
        )
        self.add_command(
            'Make rotation movie',
            command=gui.make_rotation_movie,
            state='disabled',
            can_disable=True,
        )
        
