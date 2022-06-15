from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.button import Button
from widgets.selectfilter import SelectFilter
import matplotlib.artist
import traceback
import globals
from copy import deepcopy

class ManageArtists(PopupWindow,object):
    def __init__(self,gui):
        if globals.debug > 1: print("manageartists.__init__")
        self.gui = gui
        super(ManageArtists,self).__init__(
            self.gui,
            title="Manage artists",
            oktext="Done",
            okcommand=self.close,
            cancelcommand=self.cancel,
        )
        
        self.ax = self.gui.interactiveplot.ax

        self.artists = self.ax.get_children()
        self.initial_visible = [artist for artist in self.artists if hasattr(artist, "get_visible") and artist.get_visible()]
        self.initial_hidden = [artist for artist in self.artists if hasattr(artist, "get_visible") and not artist.get_visible()]
        self.visible_artists = [artist for artist in self.artists if hasattr(artist, "get_visible") and artist.get_visible()]
        self.hidden_artists = [artist for artist in self.artists if hasattr(artist, "get_visible") and not artist.get_visible()]

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.selectfilter.bind("<<ValuesUpdated>>", self.update_artists,add="+")
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_variables")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_widgets")
        self.selectfilter = SelectFilter(
            self.contents,
            left=self.visible_artists,
            right=self.hidden_artists,
            labels=("Visible Artists", "Hidden Artists"),
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.place_widgets")
        self.selectfilter.pack(fill='both',expand=True)
        
    def update_artists(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.update_artists")
        for artist in self.selectfilter.left: artist.set_visible(True)
        for artist in self.selectfilter.right: artist.set_visible(False)
        self.ax.get_figure().canvas.draw_idle()

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.cancel")
        self.selectfilter.update_values(
            left=self.initial_visible,
            right=self.initial_hidden,
        )
        self.close()

