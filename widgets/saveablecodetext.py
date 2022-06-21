import sys
from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.codetext import CodeText
from widgets.button import Button
from widgets.warningmessage import WarningMessage
import matplotlib.artist
import traceback
import globals
import os
import json


class SaveableCodeText(CodeText, object):
    forbidden_characters = ["#","%","&","{","}","\\","<",">","*","?","/"," ","$","!","'",'"',":","@","+","`","|","="]
    def __init__(self, master, directory, **kwargs):
        self.directory = directory
        if not os.path.isdir(self.directory): os.mkdir(self.directory)

        self.frame = tk.Frame(master)
        super(SaveableCodeText,self).__init__(self.frame,**kwargs)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.pack = self.frame.pack
        self.grid = self.frame.grid
        self.place = self.frame.place

        self.update_combobox_list()
        self.combobox.configure(
            validate='focusout',
            validatecommand=(self.combobox.register(self.validatecommand), '%P'),
        )

        self.bind("<Key>", self.mark_dirty, add='+')
        self.combobox.bind("<<ComboboxSelected>>", self.load, add="+")
        self.combobox.bind("<Return>", lambda *args, **kwargs: self.focus(), add="+")

        self.combobox.focus()
        
        self.saved = False
        self.previous_name = None

    def create_variables(self, *args, **kwargs):
        self.combobox_text = tk.StringVar()

    def create_widgets(self, *args, **kwargs):
        self.top_frame = tk.Frame(self.frame)
        self.label = ttk.Label(self.top_frame, text="Name:")
        self.combobox = ttk.Combobox(self.top_frame,textvariable=self.combobox_text)
        self.save_button = Button(self.top_frame,text="Save",command=self.save)

    def place_widgets(self,*args,**kwargs):
        self.label.pack(side='left')
        self.combobox.pack(side='left',fill='both',expand=True,padx=5)
        self.save_button.pack(side='left')
        self.top_frame.pack(side='top',fill='both',expand=True)
        self.pack(side='top',fill='both',expand=True)

    def mark_dirty(self, *args, **kwargs):
        self.saved = False
        
    def save(self, *args, **kwargs):
        value = self.combobox_text.get()
        filename = os.path.join(self.directory,value+".json")
        obj = self.get('0.0','end')
        with open(filename,'w') as f:
            json.dump(obj, f, indent=4)
        self.saved = True
        self.update_combobox_list()
        
    def load(self, event=None, name=None):
        self.combobox.selection_clear()
        if name is None: name = self.combobox.get()

        path = os.path.join(self.directory,name+".json")
        if not os.path.isfile(path):
            raise RuntimeError("Failed to find file '"+path+"'")

        with open(path,'r') as f:
            code = json.load(f)
        if code == self.get('0.0','end'): return
        
        true_previous_name = self.previous_name
        if not self.saved:
            self.combobox_text.set(true_previous_name)
            if not self.ask_continue_without_saving():
                return
        self.combobox_text.set(name)
        self.previous_name = name
        self.delete('1.0','end')
        self.insert('0.0', code)
        self.saved = True

    def ask_continue_without_saving(self, message="You have unsaved changes. Continue?"):
        msgbox = tk.messagebox.askquestion(master=self.master,title="Continue without saving?", message=message, icon='warning',parent=self)
        return msgbox == "yes"
        
    def update_combobox_list(self,*args,**kwargs):
        if globals.debug > 1: print("addartist.update_combobox_list")
        names = [name.replace(".json","") for name in os.listdir(self.directory)]
        self.combobox.configure(values=names)

    def validatecommand(self, text):
        for char in SaveableCodeText.forbidden_characters:
            if char in text:
                print("Forbidden characters in artist names are: "+" ".join(SaveableCodeText.forbidden_characters))
                self.error("Invalid artist name. See terminal.", terminal=False)
                self.combobox.focus()
                return False
        self.previous_name = text
        return True
