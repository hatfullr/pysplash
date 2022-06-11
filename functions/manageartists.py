from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.listboxscrollbar import ListboxScrollbar
from widgets.button import Button
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
            okcommand=self.update_artists,
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.ax = self.gui.interactiveplot.ax

        self.artists = self.ax.get_children()
        self.visible_artists = []
        self.hidden_artists = []

        left_idx = 0
        right_idx = 0
        for artist in self.artists:
            if artist.get_visible():
                self.visible_artists.append(artist)
                self.listbox_left.insert(left_idx, str(artist))
                left_idx += 1
            else:
                self.hidden_artists.append(artist)
                self.listbox_right.insert(right_idx, str(artist))
                right_idx += 1
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_variables")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.create_widgets")
        self.left_frame = tk.Frame(self.contents)
        self.middle_frame = tk.Frame(self.contents)
        self.right_frame = tk.Frame(self.contents)

        self.label_left = ttk.Label(self.left_frame,text="Shown Artists",anchor='center')
        self.label_right = ttk.Label(self.right_frame,text="Hidden Artists",anchor='center')
        
        self.listbox_left = ListboxScrollbar(self.left_frame,selectmode='extended')
        self.listbox_right = ListboxScrollbar(self.right_frame,selectmode='extended')

        self.left_button = Button(self.middle_frame,text="<",width=2,command=self.move_selected_left)
        self.right_button = Button(self.middle_frame,text=">",width=2,command=self.move_selected_right)

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.place_widgets")

        self.label_left.pack(side='top',fill='x',expand=True)
        self.label_right.pack(side='top',fill='x',expand=True)
        
        self.listbox_left.pack(side='top',fill='both',expand=True)
        self.listbox_right.pack(side='top',fill='both',expand=True)

        self.right_button.pack(side='top',pady=(0,2.5))
        self.left_button.pack(side='top',pady=(2.5,0))
        
        self.left_frame.pack(side='left',fill='both',expand=True)
        self.middle_frame.pack(side='left',padx=5)
        self.right_frame.pack(side='left',fill='both',expand=True)

    def update_artists(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists.update_artists")
        for artist in self.hidden_artists:
            artist.set_visible(False)
        for artist in self.visible_artists:
            artist.set_visible(True)
        self.ax.get_figure().canvas.draw_idle()
        self.close()

    def _update_listboxes(self,*args,**kwargs):
        if globals.debug > 1: print("manageartists._update_listboxes")
        self.listbox_left.delete(0,'end')
        for i, artist in enumerate(self.visible_artists):
            self.listbox_left.insert(i, artist)
        self.listbox_right.delete(0,'end')
        for i, artist in enumerate(self.hidden_artists):
            self.listbox_right.insert(i, artist)

    def move_selected_left(self, *args, **kwargs):
        if globals.debug > 1: print("manageartists.move_selected_left")
        indices = self.listbox_right.curselection()
        to_remove = []
        for i in indices:
            self.visible_artists.append(self.hidden_artists[i])
            to_remove.append(self.hidden_artists[i])
        self.hidden_artists = [e for e in self.hidden_artists if e not in to_remove]
        self._update_listboxes()
        self.listbox_right.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.listbox_right.get(0,'end'))-1))
            self.listbox_right.select_set(next_item)
            self.listbox_right.event_generate("<<ListboxSelect>>")
        
    def move_selected_right(self, *args, **kwargs):
        if globals.debug > 1: print("manageartists.move_selected_right")
        indices = self.listbox_left.curselection()
        to_remove = []
        for i in indices:
            self.hidden_artists.append(self.visible_artists[i])
            to_remove.append(self.visible_artists[i])
        self.visible_artists = [e for e in self.visible_artists if e not in to_remove]
        self._update_listboxes()
        self.listbox_left.focus()
        if len(indices) == 1: # If we only moved 1 item, try setting the selection to the next item
            next_item = max(0,min(indices[0], len(self.listbox_left.get(0,'end'))-1))
            self.listbox_left.select_set(next_item)
            self.listbox_left.event_generate("<<ListboxSelect>>")
        
