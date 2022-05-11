from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.button import Button
import globals


class PopupWindow(tk.Toplevel, object):
    def __init__(self, master, title="", resizeable=(False,False), oktext="Ok", okcommand=None, canceltext="Cancel", cancelcommand=None, pad=5, *args, **kwargs):
        if globals.debug > 1: print("popupwindow.__init__")

        # Setup the window
        super(PopupWindow, self).__init__(master,*args,**kwargs)

        self.root = self.master.winfo_toplevel()

        self.pad = pad
        aspect = self.root.winfo_screenheight()/self.root.winfo_screenwidth()
        self._width = int(self.root.winfo_screenwidth() / 6.)
        self._height = int(self._width*aspect)

        self.withdraw()

        self.protocol("WM_DELETE_WINDOW",self.close)
        self.resizable(resizeable[0],resizeable[1])

        self.title(title)
        center_x = int(self.root.winfo_rootx() + 0.5*self.root.winfo_width() - 0.5*self._width)
        center_y = int(self.root.winfo_rooty() + 0.5*self.root.winfo_height() - 0.5*self._height)
        self.geometry("+%d+%d" % (center_x, center_y))
        self.configure(padx=self.pad,pady=self.pad)
        self.minsize(self._width,0)
        self.maxsize(self._width, self._height)

        # Create the contents frame
        self.contents = tk.Frame(self)
        
        # Create the ok and cancel buttons
        buttons_frame = tk.Frame(self)
        
        if okcommand is None:
            Button(buttons_frame,text=oktext).pack(side='left')
        else:
            Button(buttons_frame,text=oktext,command=okcommand).pack(side='left')
            
        if cancelcommand is None:
            Button(buttons_frame,text=canceltext,command=self.close).pack(side='left',padx=(self.pad,0))
        else:
            Button(buttons_frame,text=canceltext,command=cancelcommand).pack(side='left',padx=(self.pad,0))
        
        # Place the widgets
        self.contents.pack(side='top',padx=0,pady=(0,self.pad))
        buttons_frame.pack(side='bottom',anchor='e',padx=0,pady=0)

        # Now show the window
        self.deiconify()

    def close(self,*args,**kwargs):
        if globals.debug > 1: print("popupwindow.close")
        self.destroy()
