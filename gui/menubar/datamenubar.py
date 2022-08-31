from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.importdata import ImportData
from functions.downloaddatafromserver import DownloadDataFromServer
from functions.findparticle import FindParticle
from functions.hotkeystostring import hotkeys_to_string
from gui.menubar.menu import Menu

class DataMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        super(DataMenuBar, self).__init__(
            master,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        label = "Import data "+hotkeys_to_string("import data")
        self.add_command(label='Download data from server', command=lambda: DownloadDataFromServer(gui))
        self.add_command(label="Find particle", command = lambda: FindParticle(gui))
        self.add_command(label=label, command=lambda: ImportData(gui))
        
        
