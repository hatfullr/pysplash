from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    import tkFileDialog
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.filedialog as tkFileDialog
import os.path
from glob import glob
from widgets.flashingentry import FlashingEntry
from widgets.button import Button

# This class consists of an entry widgets and a "Browse" button for file paths
class PathEntry(tk.Frame, object):
    modes = ["open filename","open filenames","save as filename","directory"]
    modes_str = ",".join(["'"+m+"'" for m in modes])
    def __init__(self, master, mode, textvariable=None, initialfile="", initialdir="", filetypes=(), defaultextension="", multiple=True, pad=5, *args, **kwargs):
        if mode not in PathEntry.modes:
            raise ValueError("mode '"+mode+"' must be one of "+PathEntry.modes_str)
        self.mode = mode
        self.textvariable = textvariable

        self.dialogkwargs = {
            'initialfile' : initialfile,
            'initialdir' : initialdir,
            'filetypes' : filetypes,
            'defaultextension' : defaultextension,
            'multiple' : multiple,
        }
        
        if self.textvariable is None: self.textvariable = tk.StringVar()
        self.bid = None

        super(PathEntry, self).__init__(master)
        self._entry = FlashingEntry(self,textvariable=self.textvariable,*args,**kwargs)
        self._entry.configure(validate='focusout',validatecommand=(self._entry.register(self.validatecommand),'%P'))
        self._entry.pack(side='left',fill='both',expand=True,padx=(0,pad))
        Button(self,text='Browse',command=self._browse).pack(side='left',anchor='e',fill='y')

        self.bind("<<ValidateFail>>", self.on_validate_fail,add="+")
        self.bind("<<ValidateSuccess>>", self.on_validate_success,add="+")

    def get(self, *args, **kwargs):
        paths = self.textvariable.get()
        if isinstance(paths, str):
            if "'" in paths:
                paths = paths.split("'")[1::2]
            else:
                paths = self._text_to_paths(paths)
        final = []
        for path in paths:
            for p in sorted(glob(path)): final.append(p)
        return final
    
    def set(self, path, *args, **kwargs):
        self.textvariable.set(path)
        
    def _browse(self, *args, **kwargs):
        if self.mode == "open filename":
            path = tkFileDialog.askopenfilename(**self.dialogkwargs)
        elif self.mode == "open filenames":
            path = tkFileDialog.askopenfilenames(**self.dialogkwargs)
        elif self.mode == "save as filename":
            path = tkFileDialog.asksaveasfilename(**self.dialogkwargs)
        elif self.mode == "directory":
            path = tkFileDialog.askdirectory(**self.dialogkwargs)
        else:
            raise RuntimeError("Found a mode '"+self.mode+"' but expected one of "+PathEntry.modes_str)
        if path: self.set(path)

    def _text_to_paths(self, text):
        paths = []
        substr = ""
        for i,char in enumerate(text.strip()):
            substr += char
            if char == " " and i > 0 and text[i-1] not in ["\\", " "]:
                paths.append(substr[:-1])
                substr = ""
        if substr != "": paths.append(substr)
        return paths

    def validate(self,*args,**kwargs):
        return self.validatecommand(self.textvariable.get())

    def validatecommand(self, newtext):
        if newtext == "":
            self.event_generate("<<ValidateSuccess>>")
            return True

        paths = self.get()
        for path in paths:
            if not os.path.isfile(path):
                self.on_validate_fail()
                # Also highlight the problem text
                idx = newtext.index(path)
                self._entry.selection_range(idx,idx+len(path))
                print("File name '"+path+"' not found")
                self.event_generate("<<ValidateFail>>")
                return False

        self.event_generate("<<ValidateSuccess>>")
        return True
    
    def on_validate_fail(self, time=None, *args, **kwargs):
        if time is None: self._entry.flash()
        else: self._entry.flash(time=time)
        def command(*args, **kwargs):
            self._entry.focus()
        self.bid = self._entry.bind("<FocusOut>", command)
        
    
    def on_validate_success(self, *args, **kwargs):
        if self.bid: self._entry.unbind("<FocusOut>", self.bid)
        self.bid = None
        # Make sure the widget stops flashing
        if self._entry.flashing: self._entry._stop_flash()
        
