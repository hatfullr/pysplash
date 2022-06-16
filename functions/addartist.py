import sys
from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.codetext import CodeText
from widgets.button import Button
from widgets.warningmessage import WarningMessage
from widgets.saveablecodetext import SaveableCodeText
import matplotlib.artist
import traceback
import globals
import os
import importlib
import json


class AddArtist(PopupWindow,object):
    tmp_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
    artist_directory = os.path.join(globals.profile_path,"artists")
    forbidden_characters = ["#","%","&","{","}","\\","<",">","*","?","/"," ","$","!","'",'"',":","@","+","`","|","="]
    def __init__(self, gui):
        if globals.debug > 1: print("addartist.__init__")
        self.gui = gui
        super(AddArtist,self).__init__(
            self.gui,
            title="Add artist",
            oktext="Add",
            okcommand=self.add_artist,
        )

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.codetext.insert('0.0',"def artist(ax):\n    "+"\n    ".join(globals.exec_imports)+"\n    return None")
        
        self._after_id = None
        self.previous_value = None

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_variables")
        self.error_text = tk.StringVar(value="")

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_widgets")

        self.description = ttk.Label(
            self.contents,
            text="Write any Python Matplotlib plotting code within the function 'artist' below. This function will be called to obtain the new artist and thus the function must return a Matplotlib Artist.\nEnter a new name for this artist or select a saved pre-made artist from the dropdown box to get started. If you choose a pre-made artist then the 'Add' button will overwrite that artist and add it to the plot. You can delete a pre-made artist by removing the .json file that corresponds with that artist's name in "+AddArtist.artist_directory+".",
            wraplength = self.width-2*self.cget('padx'),
            justify='left',
        )
        self.codetext = SaveableCodeText(self.contents, os.path.join(globals.profile_path,"artists"))
        self.error_label = ttk.Label(self.buttons_frame,textvariable=self.error_text)

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.place_widgets")

        self.description.pack(side='top',fill='x',pady=(0,self.cget('pady')))
        self.codetext.pack(side='top',fill='both',expand=True)
        self.error_label.pack(side='left',fill='x',expand=True)
    
    def add_artist(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.add_artist")

        if not self.codetext.saved:
            if not self.codetext.ask_continue_without_saving(): return
        
        ax = self.gui.interactiveplot.ax
        
        # Evaluate the Python script given in the CodeText block
        code = self.codetext.get('0.0','end')
        
        filename = os.path.join(AddArtist.tmp_directory,"code.py")

        if os.path.isfile(filename): os.remove(filename)
        with open(filename,'w') as f:
            f.write(code)

        if version_info.major >= 3 and version_info.minor >= 5:
            spec = importlib.util.spec_from_file_location("code.artist", filename)
            foo = importlib.util.module_from_spec(spec)
            sys.modules["code.artist"] = foo
            spec.loader.exec_module(foo)
            method = foo.artist
        elif version_info.major >= 3 and version_info.minor < 5:
            foo = importlib.machinery.SourceFileLoader("code.artist", filename).load_module()
            method = foo.artist
        else:
            import imp
            foo = imp.load_source("code.artist", filename)
            method = foo.artist


        try:
            artist = method(ax)
        except:
            print(traceback.format_exc())
            self.error("Error. See terminal for traceback", terminal=False)

        if not isinstance(artist, matplotlib.artist.Artist):
            self.error(text="'artist' must be type '"+matplotlib.artist.Artist.__name__+"', not '"+type(artist).__name__+"'")
            return
        
        ax.add_artist(artist)
        ax.get_figure().canvas.draw_idle()
        self.close()

    def error(self, text="", duration=5000, terminal=True):
        if globals.debug > 1: print("addartist.error")
        if terminal: print(text)
        self.error_text.set(text)

        if self._after_id is not None: self.after_cancel(self._after_id)
        self._after_id = self.after(duration, self.clear_error)

    def clear_error(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.clear_error")
        
        if self._after_id is not None: self.after_cancel(self._after_id)
        self._after_id = None
        self.error_text.set("")
