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
from widgets.selectfilter import SelectFilter
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import traceback
import read_file

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

        self.pathentry.bind("<<ValidateSuccess>>", self.on_validate_success, add="+")
        self.pathentry.bind("<<ValidateFail>>", self.on_validate_fail, add="+")

        #self.pathentry._entry.bind("<Return>", lambda *args, **kwargs: self.okbutton.invoke(), add="+")

        self.deiconify()
        self.pathentry._entry.focus()

    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.create_variables")
        self.path = StringVar(self, None, 'path')
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Specify below a list of files to import. Once imported, all data currently loaded in PySplash will be unloaded and inaccessible to PySplash. The list you provide should be separated by spaces and can include wildcard search patterns such as file*.dat.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )
        self.pathentry = PathEntry(
            self.contents,
            "open filenames",
            textvariable=self.path,
        )
        self.selectfilter = SelectFilter(
            self.contents,
            labels=("Unused Files", "Used Files"),
            selectmode=("extended","extended"),
            right=self.gui.filenames,
            sort=(True,True),
        )
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.place_widgets")
        self.description.pack(side='top',fill='both',expand=True)
        self.pathentry.pack(side='top',fill='x',expand=True)
        self.selectfilter.pack(side='top',fill='both',expand=True)
        
    def import_data(self,*args,**kwargs):
        if globals.debug > 1: print("importdata.import_data")
        # The value of the path entry is always a list when mode = "open filenames"
        
        # If the user currently has a plot shown, check with them first
        # to make sure it is okay that we will overwrite their plot
        currentfile = self.gui.filecontrols.current_file.get()
        for filename in self.selectfilter.right:
            if os.path.realpath(filename) == os.path.realpath(currentfile):
                break
        else:
            if self.gui.interactiveplot.drawn_object is not None:
                choice = tk.messagebox.askquestion(master=self,title="Overwrite Plot",message="Importing this list of files will erase the current plot because the data file used to create the current plot was not included. Do you wish to proceed?")
                # The choice will be one of "yes", "no", or "cancel"
                if choice != "yes": return

        self.gui.filenames = self.selectfilter.right
        self.gui.initialize()
        self.close()

    def on_validate_success(self,*args,**kwargs):
        for i, name in enumerate(self.pathentry.get()):
            if read_file.get_method(name) is None:
                print("File '"+name+"' does not match any of the accepted patterns in read_file")
                self.pathentry.event_generate("<<ValidateFail>>")
                return "break"
        
        self.selectfilter.left = self.pathentry.get()
        self.okbutton.configure(state='normal')
        for i, val in enumerate(self.selectfilter.left):
            self.selectfilter.listbox_left.itemconfig(i,background='')

    def on_validate_fail(self, *args, **kwargs):
        self.selectfilter.left = self.pathentry.get()
        self.okbutton.configure(state='disabled')
        seen = False
        for i, path in enumerate(self.selectfilter.left):
            if not os.path.isfile(path) or read_file.get_method(path) is None:
                if not seen:
                    self.selectfilter.listbox_left.see(i)
                    seen = True
                self.selectfilter.listbox_left.itemconfig(i,background='red')
        return "break"

        
