from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk
from gui.menubar.menu import Menu
from functions.hotkeystostring import hotkeys_to_string

class FileMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        self.gui = gui
        super(FileMenuBar, self).__init__(
            master,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(label='Save '+hotkeys_to_string('save'), command=self.gui.plottoolbar.save_figure)
        self.add_command(label='Save As...', command=self.gui.plottoolbar.save_figure_as)

