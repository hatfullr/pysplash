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
import matplotlib.artist
import traceback
import globals
import os
import importlib
import json


class AddArtist(PopupWindow,object):
    tmp_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
    artist_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"artists")
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

        self.name_combobox.configure(
            validate='focusout',
            validatecommand=(self.name_combobox.register(self.validatecommand), '%P'),
        )

        self.update_combobox_list()
        
        self.name_combobox.bind("<<ComboboxSelected>>", self.load_artist, add="+")
        self.name_combobox.bind("<Return>", lambda *args, **kwargs: self.codetext.focus(), add="+")

        self.codetext.insert('0.0',"def artist(ax):\n    "+"\n    ".join(globals.exec_imports)+"\n    return None")

        self.name_combobox.focus()
        
        self._after_id = None
        self.previous_value = None

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_variables")
        self.error_text = tk.StringVar(value="")
        self.combobox_text = tk.StringVar(value="")

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.create_widgets")

        self.description = ttk.Label(
            self.contents,
            text="Write any Python Matplotlib plotting code within the function 'artist' below. This function will be called to obtain the new artist and thus the function must return a Matplotlib Artist.\nEnter a new name for this artist or select a saved pre-made artist from the dropdown box to get started. If you choose a pre-made artist then the 'Add' button will overwrite that artist and add it to the plot. You can delete a pre-made artist by removing the .json file that corresponds with that artist's name in "+AddArtist.artist_directory+".",
            wraplength = self.width-2*self.cget('padx'),
            justify='left',
        )
        self.name_frame = tk.Frame(self.contents)
        self.name_label = ttk.Label(self.name_frame,text="Name:")
        self.name_combobox = ttk.Combobox(self.name_frame,textvariable=self.combobox_text)
        self.name_save = Button(self.name_frame,text="Save",command=self.save_artist)
        self.codetext = CodeText(self.contents)

        self.error_label = ttk.Label(self.buttons_frame,textvariable=self.error_text)

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.place_widgets")

        self.description.pack(side='top',fill='x',pady=(0,self.cget('pady')))

        self.name_label.pack(side='left')
        self.name_combobox.pack(side='left',fill='both',expand=True,padx=5)
        self.name_save.pack(side='left')
        self.name_frame.pack(side='top',fill='x',expand=True)
        
        self.codetext.pack(side='top',fill='both',expand=True)
        self.error_label.pack(side='left',fill='x',expand=True)

    def get_saved_artists(self, *args, **kwargs):
        if globals.debug > 1: print("addartist.get_saved_artists")

        if not os.path.isdir(AddArtist.artist_directory):
            os.mkdir(AddArtist.artist_directory)
        filenames = os.listdir(AddArtist.artist_directory)
        names = []
        methods = []
        for filename in filenames:
            with open(os.path.join(AddArtist.artist_directory,filename),'r') as f:
                obj = json.load(f)
                names.append(obj['name'])
                methods.append(obj['method'])
        return names, methods

    def update_combobox_list(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.update_combobox_list")
        self.names, self.methods = self.get_saved_artists()
        self.name_combobox.configure(values=self.names)

    def validatecommand(self, text):
        if globals.debug > 1: print("addartist.validatecommand")
        for char in AddArtist.forbidden_characters:
            if char in text:
                print("Forbidden characters in artist names are: "+" ".join(AddArtist.forbidden_characters))
                self.error("Invalid artist name. See terminal.", terminal=False)
                self.name_combobox.focus()
                return False
        self.previous_value = text
        return True

    def load_artist(self,newtext):
        if globals.debug > 1: print("addartist.load_artist")
        self.name_combobox.selection_clear()
        value = self.name_combobox.get()
        true_previous_value = self.previous_value
        if not self.is_artist_saved():
            if not self.ask_continue_without_saving():
                self.combobox_text.set(true_previous_value)
                return
        self.previous_value = value
        self.codetext.delete('1.0','end')
        self.codetext.insert('0.0', self.methods[self.names.index(value)])

    def is_artist_saved(self, *args, **kwargs):
        if globals.debug > 1: print('addartist.is_artist_saved')
        #value = self.name_combobox.get()
        if self.previous_value in self.names:
            return self.codetext.get('0.0','end').strip() == self.methods[self.names.index(self.previous_value)].strip()
        return False
            
    def save_artist(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.save_artist")
        
        value = self.name_combobox.get()
        filename = os.path.join(AddArtist.artist_directory,value+".json")
        obj = {
            'name' : value,
            'method' : self.codetext.get('0.0','end')
        }
        with open(filename,'w') as f:
            json.dump(obj, f, indent=4)
        self.update_combobox_list()

    def ask_continue_without_saving(self, message="You have unsaved changes. Continue?"):
        if globals.debug > 1: print("addartist.ask_continue_without_saving")
        msgbox = tk.messagebox.askquestion("Continue without saving?", message, icon='warning',parent=self)
        return msgbox == "yes"
    
    def add_artist(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.add_artist")

        if not self.is_artist_saved():
            if self.ask_continue_without_saving(message="Do you want to save your artist to the list of pre-made artists?"):
                self.save_artist()
        
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
            self.error(text="'artist' is type '"+type(artist).__name__+"', not '"+matplotlib.artist.Artist.__name__+"'")
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