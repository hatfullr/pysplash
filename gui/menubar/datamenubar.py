from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.downloaddatafromserver import download_data_from_server
from functions.importdata import importdata

class DataMenuBar(tk.Menu, object):
    def __init__(self, master, gui, name='data', tearoff=0, *args, **kwargs):
        super(DataMenuBar, self).__init__(
            master,
            *args,
            name=name,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(label="Import", command=lambda: importdata(gui))
        self.add_command(label='Download data from server', command=lambda: download_data_from_server(gui))
        
