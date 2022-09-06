from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.autosizelabel import AutoSizeLabel
from widgets.button import Button
from widgets.tooltip import ToolTip
import os


class About(PopupWindow,object):
    def __init__(self,gui):
        self.gui = gui
        super(About,self).__init__(
            self.gui,
            title="About",
            canceltext="Close",
            name='about',
        )

        self.okbutton.pack_forget()

        self.create_widgets()
        self.place_widgets()
        
    def create_widgets(self,*args,**kwargs):
        self.current_directory_frame = tk.LabelFrame(
            self.contents,
            text="Current working directory",
        )
        self.current_directory = AutoSizeLabel(
            self.current_directory_frame,
            text=os.getcwd(),
            truncate='left',
        )
        self.copy_current_directory_button = Button(
            self.current_directory_frame,
            text="Copy",
            command=self.copy_current_directory,
        )
        ToolTip.createToolTip(
            self.copy_current_directory_button,
            "If using Linux, to paste into a terminal you must press Ctrl+Shift+V instead of the middle mouse button"
        )
        
        self.author_frame = tk.LabelFrame(
            self.contents,
            text="Author",
        )
        self.author = ttk.Label(
            self.author_frame,
            text="Roger Hatfull, University of Alberta",
        )
        
    def place_widgets(self,*args,**kwargs):
        self.copy_current_directory_button.pack(side='right',padx=5,pady=5)
        self.current_directory.pack(side='left',fill='x',expand=True)
        
        self.current_directory_frame.pack(side='top',fill='x',expand=True)
        self.author.pack(fill='both',expand=True)
        self.author_frame.pack(side='top',fill='x',expand=True)

    def copy_current_directory(self,*args,**kwargs):
        self.gui.clipboard_clear()
        self.gui.clipboard_append(os.getcwd())

        
