from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

from functions.addartist import AddArtist
from functions.manageartists import ManageArtists
from functions.setstyle import SetStyle

class PlotMenuBar(tk.Menu, object):
    def __init__(self, master, gui, name='functions', tearoff=0, *args, **kwargs):
        super(PlotMenuBar, self).__init__(
            master,
            *args,
            name=name,
            tearoff=tearoff,
            **kwargs
        )

        self.add_command(label='Add artist', command=lambda *args,**kwargs: AddArtist(gui))
        self.add_command(label='Manage artists', command=lambda *args,**kwargs: ManageArtists(gui))
        self.add_command(label='Set style', command=lambda *args,**kwargs: SetStyle(gui))

        
