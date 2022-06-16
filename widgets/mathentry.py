from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

from widgets.flashingentry import FlashingEntry
from widgets.button import Button
from widgets.popupwindow import PopupWindow
from widgets.saveablecodetext import SaveableCodeText
import globals
import numpy as np
import traceback
import os

# This widget expects as input some math operation using the data in the gui
# widget. For example "rho * opacity" would multiply together the "rho" and
# "opacity" columns in the gui's data.

class MathEntry(FlashingEntry, object):
    def __init__(self, master, gui, *args, **kwargs):
        self.allowempty = kwargs.pop('allowempty',True)
        frame = tk.Frame(master)
        super(MathEntry, self).__init__(frame, *args, **kwargs)
        self.gui = gui
        self.configure(validate='focusout',validatecommand=(self.register(self.validatecommand),'%P'))
        self.bid = None

        self.rich_edit_button = Button(
            frame,
            text="...",
            command=self.show_rich_edit,
            width=2,
        )
        self.pack(side='left',fill='both',expand=True)
        self.rich_edit_button.pack(side='left')
        self.using_rich_edit = False
        def onfocusin(*args,**kwargs): self.using_rich_edit = False
        self.bind("<FocusIn>", lambda *args, **kwargs: onfocusin)

        self.pack = frame.pack
        self.grid = frame.grid
        self.place = frame.place

        self.bind("<<ValidateFail>>", self.on_validate_fail,add="+")
        self.bind("<<ValidateSuccess>>", self.on_validate_success,add="+")

    def show_rich_edit(self, *args, **kwargs):
        self.using_rich_edit = True
        
        def okcommand(*args, **kwargs):
            text = codetext.get("1.0", "end-1c")
            if self.validatecommand(text):
                window.close()
                self.delete(0,'end')
                self.insert(0,text)
                self.using_rich_edit = False
                self.event_generate("<<MathEntrySaved>>")
            
        window = PopupWindow(
            self,
            title="Edit entry...",
            oktext='Apply',
            okcommand=okcommand,
            height=int(self.winfo_screenheight() / 2.),
        )
        description = ttk.Label(
            window.contents,
            text="Enter any arbitrary Python code you wish below. You can reference data variables by their names shown in the dropdown selection box, such as \"x\", \"y\", \"z\", etc. Your code must terminate with the line \"result = <your result>\" where \"<your reuslt>\" represents a 1D array.\nYou can save your code by giving it a name and clicking \"Save\".",
            wraplength = window.width - 2*window.cget('padx'),
        )

        selector_frame = tk.Frame(window.contents)
        #label = ttk.Label(selector_frame, text="Name:")
        #combobox_text = tk.StringVar()
        #combobox = ttk.Combobox(selector_frame, textvariable=combobox_text)
        #save_button = Button(selector_frame, text="Save")
        
        codetext = SaveableCodeText(window.contents, os.path.join(globals.profile_path,"axis"))
        codetext.insert('0.0', self.get())

        description.pack(side='top',fill='both')
        #label.pack(side='left')
        #combobox.pack(side='left',fill='both',expand=True,padx=5)
        #save_button.pack(side='left')
        #selector_frame.pack(side='top',fill='both',expand=True)
        codetext.pack(side='top', fill='both', expand=True)

        
    def get_variables_and_units(self, *args, **kwargs):
        # Get the keys to the data dictionary in GUI
        if self.gui.data is None: return None, None, None
        data = self.gui.data['data']
        
        variables = {key:self.gui.get_display_data(key,identifier=self.get(),scaled=False) for key in data.keys()}
        physical_units = {key:np.array([self.gui.get_physical_units(key)]) for key in data.keys()}
        display_units = {key:np.array([self.gui.get_display_units(key)]) for key in data.keys()}

        return variables, physical_units, display_units
    
    def get_data(self, *args, **kwargs):
        text = kwargs.pop('text',None)
        if text is None: text = self.get()
        variables, physical_units, display_units = self.get_variables_and_units()
        if (text.strip() == "" or
            (variables is None and physical_units is None and display_units is None)):
            return None,None,None
        
        imp = "\n".join(globals.exec_imports)+"\n"
        if "result =" not in text and "result=" not in text:
            text = imp+"result = "+text
        else:
            text = imp+text

        # We feed in the unscaled variables only
        loc = {}
        exec(text, variables, loc)
        result1 = loc['result']
        loc = {}
        exec(text, physical_units, loc)
        result2 = loc['result']
        loc = {}
        exec(text, display_units, loc)
        result3 = loc['result']
        return result1, result2, result3

    def validatecommand(self, newtext):
        # Allow empty text
        if not newtext.strip() or newtext.strip() == "":
            if self.allowempty:
                self.event_generate("<<ValidateSuccess>>")
                return True
            else:
                print("Empty text is not allowed")
                self.event_generate("<<ValidateFail>>")
                return False

        try:
            self.get_data(text=newtext)
        except Exception:
            print(traceback.format_exc())
            self.event_generate("<<ValidateFail>>")
            return False
        
        self.event_generate("<<ValidateSuccess>>")
        return True
        
    def on_validate_fail(self, *args, **kwargs):
        self.flash()
        self.bid = self.bind("<FocusOut>", lambda *args, **kwargs: self.focus(),add="+")
        
    def on_validate_success(self, *args, **kwargs):
        if self.bid: self.unbind("<FocusOut>", self.bid)
        self.bid = None
        self.event_generate("<<MathEntrySaved>>")
