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
    def __init__(self, master, mode, textvariable=None, initialfile="", initialdir="", filetypes=(), defaultextension="", multiple=True, pad=5, validatecommand=None, **kwargs):
        if mode not in PathEntry.modes:
            raise ValueError("mode '"+mode+"' must be one of "+PathEntry.modes_str)
        self.mode = mode
        self.textvariable = textvariable
        self._validatecommand = validatecommand
        if validatecommand is None: self._validatecommand = self.validatecommand
        
        self.dialogkwargs = {
            'initialfile' : initialfile,
            'initialdir' : initialdir,
            'filetypes' : filetypes,
            'defaultextension' : defaultextension,
            'multiple' : multiple,
        }
        
        if self.textvariable is None: self.textvariable = tk.StringVar()

        super(PathEntry, self).__init__(master)
        self._entry = FlashingEntry(self,textvariable=self.textvariable,**kwargs)
        self._entry.configure(validate='focusout',validatecommand=(self._entry.register(self._validatecommand),'%P'))
        self._entry.pack(side='left',fill='both',expand=True,padx=(0,pad))
        self._browse_button = Button(self,text='Browse',command=self._browse)
        self._browse_button.pack(side='left',anchor='e',fill='y')

        self.bind("<<ValidateFail>>", self.on_validate_fail,add="+")
        self.bind("<<ValidateSuccess>>", self.on_validate_success,add="+")

    def configure(self,*args,**kwargs):
        self._browse_button.configure(*args,**kwargs)
        self._entry.configure(*args,**kwargs)
        
    def config(self,*args,**kwargs):
        return self.configure(*args,**kwargs)

    def get(self, *args, **kwargs):
        paths = self.textvariable.get()
        if isinstance(paths, str):
            if "'" in paths:
                paths = paths.split("'")[1::2]
            else:
                paths = self._text_to_paths(paths)
        final = []
        for path in paths:
            for p in glob(os.path.expanduser(path)):
                final.append(p)
        return final
    
    def set(self, path, *args, **kwargs):
        self.textvariable.set(path)
        
    def _browse(self, *args, **kwargs):
        if self.mode == "open filename":
            path = tkFileDialog.askopenfilename(**self.dialogkwargs)
        elif self.mode == "open filenames":
            path = tkFileDialog.askopenfilenames(**self.dialogkwargs)
        elif self.mode == "save as filename":
            self.dialogkwargs.pop('multiple')
            path = tkFileDialog.asksaveasfilename(**self.dialogkwargs)
        elif self.mode == "directory":
            path = tkFileDialog.askdirectory(**self.dialogkwargs)
        else:
            raise RuntimeError("Found a mode '"+self.mode+"' but expected one of "+PathEntry.modes_str)
        if path:
            cwd = os.getcwd()
            if isinstance(path, (list, tuple)):
                path = [os.path.basename(p) if cwd in p else p for p in path]
            elif cwd in path: path = os.path.basename(path)
            self.set(path)
            self.validate()

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
        return self._validatecommand(self.textvariable.get())

    def validatecommand(self, newtext):
        if newtext == "":
            self.event_generate("<<ValidateSuccess>>")
            return True

        paths = self.get()
        for path in paths:
            if not os.path.isfile(path):
                print("File name '"+path+"' not found")
                self.event_generate("<<ValidateFail>>")
                return False

        self.event_generate("<<ValidateSuccess>>")
        return True
    
    def on_validate_fail(self, *args, **kwargs):
        self._entry.flash()
    
    def on_validate_success(self, *args, **kwargs):
        # Make sure the widget stops flashing
        if self._entry.flashing: self._entry._stop_flash()
        
