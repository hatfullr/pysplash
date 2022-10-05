from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

from widgets.artisteditor import ArtistEditor
from widgets.verticalscrolledframe import VerticalScrolledFrame
from widgets.listboxscrollbar import ListboxScrollbar
from widgets.treeviewscrollbar import TreeviewScrollbar

import matplotlib

# A frame which contains a listbox on the left and settings on the
# right, where the listbox is filled with artists

class MultiArtistEditor(tk.Frame, object):
    def __init__(self, gui, master, artists, *args, **kwargs):
        self.gui = gui
        if not isinstance(artists, dict):
            raise TypeError("artists must be a dict")
        super(MultiArtistEditor,self).__init__(master,*args,**kwargs)
        
        self.create_widgets()
        self.place_widgets()

        # Populate the listbox
        #self.listbox.delete(0,'end')
        #for i,name in enumerate(artists.keys()):
        #    self.listbox.insert(i,name)
        for i,name in enumerate(artists.keys()):
            self.treeview.insert("","end",artists[name],text=name)

        # Create the artist editors
        self.artist_editors = [ArtistEditor(self.gui,self.editor_frame,artist,name) for name,artist in artists.items()]

        self.current_editor = None

        self.treeview.bind("<<TreeviewSelect>>", self.on_listbox_select)
        #self.listbox.bind("<<ListboxSelect>>", self.on_listbox_select)

    def create_widgets(self,*args,**kwargs):
        self.left_frame = tk.Frame(self)
        self.left_label = ttk.Label(self.left_frame,text="Artists",anchor='c')
        self.listbox_frame = tk.Frame(self.left_frame,relief='sunken',bd=1)
        self.treeview = TreeviewScrollbar(self.listbox_frame,selectmode='browse')
        #self.listbox = ListboxScrollbar(self.listbox_frame,selectmode='single')

        self.right_frame = tk.Frame(self)
        self.right_label = ttk.Label(self.right_frame,text="Settings",anchor='c')
        self.editor_frame = tk.Frame(self.right_frame,relief='sunken',bd=1)
        
    def place_widgets(self,*args,**kwargs):
        self.left_label.pack(side='top',fill='x')
        self.listbox_frame.pack(side='top',fill='both',expand=True)
        self.treeview.pack(fill='both',expand=True)
        #self.listbox.pack(fill='both',expand=True)
        self.left_frame.pack(side='left',fill='both')

        self.right_label.pack(side='top',fill='x')
        self.editor_frame.pack(side='left',fill='both',expand=True)
        self.right_frame.pack(side='left',fill='both',expand=True)
    
    def on_listbox_select(self,*args,**kwargs):
        #curselection = self.listbox.curselection()
        curselection = self.treeview.selection()
        if len(curselection) >= 1:
            curselection = self.treeview.index(curselection[0])
            if self.current_editor is not self.artist_editors[curselection]:
                if self.current_editor is not None: self.current_editor.pack_forget()
                self.current_editor = self.artist_editors[curselection]
                self.current_editor.pack(side='right',expand=True,fill='both')
        
    def update_artists(self,*args,**kwargs):
        for editor in self.artist_editors:
            editor.update_artist()
