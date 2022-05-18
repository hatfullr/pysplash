from sys import version_info, platform
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.button import Button
from functions.closewindow import close_window
import globals


class PopupWindow(tk.Toplevel, object):
    def __init__(self, master, title="", resizeable=(False,False), oktext="Ok", okcommand=None, canceltext="Cancel", cancelcommand=None, show=True, pad=5, *args, width=None, height=None, **kwargs):
        if globals.debug > 1: print("popupwindow.__init__")
        
        # Setup the window
        super(PopupWindow, self).__init__(master,*args,**kwargs)
        self.withdraw()

        # When the user clicks on widgets etc, those widgets should acquire
        # the application focus... (why isn't this default?!)
        self.bind("<Button-1>", lambda event: event.widget.focus())

        self.root = self.master.winfo_toplevel()
        
        # If width keyword is not given, try giving it an appropriate width
        if width is None:
            self.width = int(self.root.winfo_screenwidth() / 6.)
        else: self.width = width
        
        # If height keyword is not given, then try to give an appropraite height
        if height is None:
            aspect = self.root.winfo_screenheight()/self.root.winfo_screenwidth()
            self.height = int(self.width*aspect)
        else: self.height = height

        self.protocol("WM_DELETE_WINDOW",self.close)
        self.resizable(resizeable[0],resizeable[1])

        self.title(title)
        self.configure(padx=pad,pady=pad)

        center_x = int(self.root.winfo_rootx() + 0.5*self.root.winfo_width() - 0.5*self.width)
        center_y = int(self.root.winfo_rooty() + 0.5*self.root.winfo_height() - 0.5*self.height)
        # Adjust a little bit as a guess for hte bar height of the window
        center_y -= int(self.winfo_screenheight() / 20.)
        self.geometry("+%d+%d" % (center_x, center_y))
        
        self.minsize(self.width,0)
        self.maxsize(self.width, self.winfo_screenheight())

        # Create the contents frame
        self.contents = tk.Frame(self)
        
        # Create the ok and cancel buttons
        self.buttons_frame = tk.Frame(self)
        
        if okcommand is None:
            self.okbutton = Button(self.buttons_frame,text=oktext)
        else:
            self.okbutton = Button(self.buttons_frame,text=oktext,command=okcommand)
            
        if cancelcommand is None:
            self.cancelbutton = Button(self.buttons_frame,text=canceltext,command=self.close)
        else:
            self.cancelbutton = Button(self.buttons_frame,text=canceltext,command=cancelcommand)
        
        self.cancelbutton.pack(side='right',padx=(pad,0))
        self.okbutton.pack(side='right')
        
        # Place the widgets
        self.contents.pack(side='top',fill='both',expand=True,pady=(0,pad))
        self.buttons_frame.pack(side='bottom',anchor='e',fill='both',expand=True)

        # Now show the window
        if show: self.deiconify()

    def close(self,*args,**kwargs):
        if globals.debug > 1: print("popupwindow.close")
        close_window(self)
