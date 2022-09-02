from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.selectfilter import SelectFilter
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import inspect
import matplotlib
import globals
import traceback
import warnings
import ast


class SetStyle(PopupWindow,object):
    default_name = "default"
    def __init__(self, gui):
        if globals.debug > 1: print("setstyle.__init__")

        self.gui = gui
        
        # Setup the window
        super(SetStyle,self).__init__(
            self.gui,
            title="Set style",
            oktext="Done",
            okcommand=self.close,
            cancelcommand=self.cancel,
            name='setstyle',
        )

        matplotlib.style.reload_library() # Make sure available styles is up-to-date
        self.available_styles = sorted(matplotlib.pyplot.style.available)
        self.available_styles = ["default"] + self.available_styles

        self.current_style = list(ast.literal_eval(self.gui.interactiveplot.style.get()))
        if self.current_style is None: self.current_style = ['default']

        for style in self.current_style:
            self.available_styles.remove(style)
        
        self.create_widgets()
        self.place_widgets()

        self.selectfilter.bind("<<ValuesUpdated>>", self.set_style, add="+")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.create_widgets")

        self.description = ttk.Label(
            self.contents,
            text="Organize the Matplotlib styles on the right under 'Current Style' by dragging and dropping with your mouse to customize the look of the plot. Styles placed above others will be used first and any unspecified parameters will then be set by styles further down the list. Please see the Matplotlib documentation for details. You can add styles by adding .mplstyle files to "+matplotlib.get_configdir()+".",
            wraplength = self.width-2*self.cget('padx'),
            justify='left',
        )
        
        self.selectfilter = SelectFilter(
            self.contents,
            left=self.available_styles,
            right=self.current_style,
            selectmode=('extended','dragdrop'),
            labels=("Available styles", "Current style"),
            sort=(True, False),
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.place_widgets")
        self.description.pack(side='top',fill='both',expand=True)
        self.selectfilter.pack(side='top',fill='both',expand=True)

    def set_style(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.set_style")
        self.gui.interactiveplot.style.set(self.selectfilter.right)

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print('setstyle.cancel')
        self.selectfilter.update_values(left=self.available_styles,right=self.current_style)
        self.close()

