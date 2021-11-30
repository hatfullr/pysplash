import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import globals
import os
    
class Window(tk.Tk):
    def __init__(self):
        if globals.debug > 1: print("window.__init__")
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.handleException
        
        tk.Tk.__init__(self)
        self.wm_title("PySplash")

        self.width = tk.IntVar(value=self.winfo_width())
        self.height = tk.IntVar(value=self.winfo_height())
        self.resizing = False
        
        self.after_id = None

        self.configure(padx=5,pady=5)
        self.bind("<Configure>",self.detect_resize)

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

        # Save preferences in the gui
        for child in self.winfo_children():
            if(hasattr(child,"save_preferences")):
                child.save_preferences()
        
        # Remove all files from the "tmp" directory
        tmp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),"tmp")
        for filename in os.listdir(tmp_path):
            os.remove(os.path.join(tmp_path,filename))
                
        self.quit()

    def on_resize(self,event):
        if globals.debug > 1: print("window.on_resize")
        self.width.set(event.width)
        self.height.set(event.height)
        self.resizing = False
        self.event_generate("<<ResizeStopped>>")
        
    def detect_resize(self,event):
        if globals.debug > 1: print("window.detect_resize")
        if event.widget is self:
            if self.width.get() != event.width or self.height.get() != event.height:
                if not self.resizing:
                    self.resizing = True
                    self.event_generate("<<ResizeStarted>>")
                if self.after_id is not None:
                    self.after_cancel(self.after_id)
                self.after_id = self.after(100,lambda event=event: self.on_resize(event))
