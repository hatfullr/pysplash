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
from widgets.multiartisteditor import MultiArtistEditor
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
            name='manageartists',
        )
        
        self.ax = self.gui.interactiveplot.ax

        self.artists = self.ax.get_children()

        # Remove any duplicate artists. This can happen for ax.plot artists, for some reason...
        self.artists = [artist for i,artist in enumerate(self.artists) if artist not in self.artists[:i]]
        
        self.initial_visible = [artist for artist in self.artists if hasattr(artist, "get_visible") and artist.get_visible()]
        self.initial_hidden = [artist for artist in self.artists if hasattr(artist, "get_visible") and not artist.get_visible()]
        self.visible_artists = [artist for artist in self.initial_visible]
        self.hidden_artists = [artist for artist in self.initial_hidden]

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        #self.selectfilter.bind("<<ValuesUpdated>>", self.update_artists,add="+")
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_variables")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_widgets")
        self.editor = MultiArtistEditor(
            self.gui,
            self.contents,
            {str(artist):artist for artist in self.artists},
        )
        
        #self.selectfilter = SelectFilter(
        #    self.contents,
        #    left=self.visible_artists,
        #    right=self.hidden_artists,
        #    labels=("Visible Artists", "Hidden Artists"),
        #)

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.place_widgets")
        self.editor.pack(fill='both',expand=True)
        #self.selectfilter.pack(fill='both',expand=True)
        
    def update_artists(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.update_artists")
        for artist in self.selectfilter.left: artist.set_visible(True)
        for artist in self.selectfilter.right: artist.set_visible(False)
        self.gui.interactiveplot.draw()

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.cancel")
        #self.selectfilter.update_values(
        #    left=self.initial_visible,
        #    right=self.initial_hidden,
        #)
        self.close()

