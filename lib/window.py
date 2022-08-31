import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from functions.closewindow import close_window
import globals
import os
import shutil

class Window(tk.Tk):
    def __init__(self):
        if globals.debug > 1: print("window.__init__")
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.handleException
        
        tk.Tk.__init__(self)
        self.wm_title("PySplash")

        self.width = self.winfo_width()
        self.height = self.winfo_height()

        self.configure(padx=5,pady=5)

    # This prevents tkinter from slowing down by first closing tkinter
    # before printing traceback whenever an error occurs
    def handleException(self, excType, excValue, trace):
        if globals.debug > 1: print("window.handleException")
        self.close()
        self.original_excepthook(excType,excValue,trace)

    def launch(self):
        if globals.debug > 1: print("window.launch")
        self.mainloop()

    def close(self,*args,**kwargs):
        if globals.debug > 1: print("window.close")
        
        # Remove all files from the "tmp" directory
        tmp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
        if os.path.isdir(tmp_path): shutil.rmtree(tmp_path)
        os.mkdir(tmp_path)
        
        close_window(self)
