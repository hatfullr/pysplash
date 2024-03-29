from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.addartist import AddArtist
from functions.manageartists import ManageArtists
from functions.setstyle import SetStyle
from gui.menubar.menu import Menu

class PlotMenuBar(Menu, object):
    def __init__(self, master, gui, tearoff=0, *args, **kwargs):
        super(PlotMenuBar, self).__init__(
            master,
            gui.window,
            *args,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(
            'Add artist',
            command=lambda *args,**kwargs: AddArtist(gui),
        )
        self.add_command(
            'Manage artists',
            command=lambda *args,**kwargs: ManageArtists(gui),
        )
        self.add_command(
            'Set style',
            command=lambda *args,**kwargs: SetStyle(gui),
        )

        
