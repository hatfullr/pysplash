from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
import os
import globals
from widgets.popupwindow import PopupWindow
from widgets.pathentry import PathEntry

def importdata(gui):
    ImportData(gui)


class ImportData(PopupWindow,object):
    def __init__(self, gui):
        if globals.debug > 1: print("importdata.__init__")

        # Setup the window
        super(ImportData,self).__init__(
            gui,
            title="Import data",
            oktext="Import",
            okcommand=self.import_data,
            show=False,
        )

        self.gui = gui

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.pathentry._entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")
        #self.bind("<Configure>", lambda *args, **kwargs: print("event"), add="+")

        self.deiconify()
        self.pathentry._entry.focus()

    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.create_variables")
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Specify below a list of files to import. Once imported, all data currently loaded in PySplash will be unloaded an inaccessible to PySplash. The list you provide should be separated by spaces and can include wildcard search patterns such as file*.dat.",
            wraplength=self._width-2*self.pad,
            justify='left',
        )
        self.pathentry = PathEntry(self.contents,"open filenames")
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.place_widgets")
        self.description.pack(side='top',fill='both',expand=True)
        self.pathentry.pack(side='top',fill='x',expand=True)

    def import_data(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.import_data")
        # First validate the path names
        if not self.pathentry.validate() or self.pathentry.textvariable.get() in [[],(),""]: return
        error = False
        
        # The value of the path entry is always a list when mode = "open filenames"

        # If the user currently has a plot shown, check with them first
        # to make sure it is okay that we will overwrite their plot
        newfilenames = self.pathentry.get()

        currentfile = self.gui.filecontrols.current_file.get()
        is_in = False
        for filename in newfilenames:
            if os.path.realpath(filename) == os.path.realpath(currentfile):
                is_in = True
                break
        
        if not is_in:
            if self.gui.interactiveplot.drawn_object is not None:
                choice = tk.messagebox.askquestion(title="Overwrite Plot",message="Importing this list of files will erase the current plot because the data file used to create the current plot was not included. Do you wish to proceed?")
                # The choice will be one of "yes", "no", or "cancel"
                if choice != "yes": return
        oldfilenames = self.gui.filenames
        self.gui.filenames = newfilenames
        try:
            self.gui.initialize()
        except ValueError as e:
            error = True
            if "does not match any of the accepted patterns in read_file" in str(e):
                print(e)
                fname = str(e).split("'")[1]
                # Also highlight the problem text
                idx = self.pathentry._entry.get().index(fname)
                self.pathentry._entry.selection_range(idx,idx+len(fname))
                self.pathentry.on_validate_fail()
                self.gui.filecontrols.current_file.set("")
                self.gui.filenames = oldfilenames
        if not error:
            self.close()