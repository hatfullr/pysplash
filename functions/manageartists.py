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
import matplotlib
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
            name='manageartists',
        )
        
        self.ax = self.gui.interactiveplot.ax
        
        self.artists = [self.ax] + self.ax.get_children()

        for a in self.gui.interactiveplot.fig.get_children():
            if a is not self.ax:
                #if isinstance(a, matplotlib.axes._base._AxesBase):
                #    self.artists += [a] + a.get_children()
                #else:
                self.artists.append(a)

        #self.artists = self.ax.get_children()

        # Remove any duplicate artists. This can happen for ax.plot artists, for some reason...
        self.artists = [artist for i,artist in enumerate(self.artists) if artist not in self.artists[:i]]
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_variables")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_widgets")
        self.editor = MultiArtistEditor(
            self.gui,
            self.contents,
            {str(artist):artist for artist in self.artists},
        )
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.place_widgets")
        self.editor.pack(fill='both',expand=True)


