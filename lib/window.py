import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import globals
    
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
