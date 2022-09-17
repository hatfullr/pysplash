from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.importdata import ImportData
from functions.downloaddatafromserver import DownloadDataFromServer
from functions.maskdata import MaskData
from gui.menubar.menu import Menu

class DataMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        super(DataMenuBar, self).__init__(
            master,
            gui.window,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(
            'Download from server',
            command=lambda *args,**kwargs: DownloadDataFromServer(gui),
            can_disable=False,
        )
        self.add_command(
            "Import",
            command=lambda *args,**kwargs: ImportData(gui),
            hotkey="import data",
            can_disable=False,
        )
        self.add_command(
            "Mask",
            command=lambda *args,**kwargs: MaskData(gui),
            state='disabled',
        )

