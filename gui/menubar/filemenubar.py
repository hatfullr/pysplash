from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk
from gui.menubar.menu import Menu

class FileMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        self.gui = gui
        super(FileMenuBar, self).__init__(
            master,
            gui.window,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(
            'Save',
            command=self.gui.plottoolbar.save_figure,
            hotkey="save",
        )
        self.add_command(
            'Save As...',
            command=self.gui.plottoolbar.save_figure_as,
        )

