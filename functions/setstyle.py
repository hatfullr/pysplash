from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.popupwindow import PopupWindow
from widgets.selectfilter import SelectFilter
import inspect
import matplotlib
import globals
import traceback
import warnings


class SetStyle(PopupWindow,object):
    default_name = "default"
    def __init__(self, gui):
        if globals.debug > 1: print("setstyle.__init__")

        self.gui = gui
        
        # Setup the window
        super(SetStyle,self).__init__(
            self.gui,
            title="Set style",
            oktext="Apply",
            okcommand=self.apply,
            cancelcommand=self.cancel,
        )

        matplotlib.style.reload_library() # Make sure available styles is up-to-date
        self.available_styles = sorted(matplotlib.pyplot.style.available)
        self.available_styles = ["default"] + self.available_styles

        self.current_style = self.gui.get_preference("style")

        if self.current_style is not None:
            for style in self.current_style:
                self.available_styles.remove(style)
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.selectfilter.bind("<<ValuesUpdated>>", self.set_style, add="+")


    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.create_variables")
        self.style_name = tk.StringVar(value=SetStyle.default_name)

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.create_widgets")

        self.description = ttk.Label(
            self.contents,
            text="Organize the Matplotlib styles below to customize the look of the plot. Styles placed above others will be used first and any unspecified parameters will then be set by styles further down the list. Please see the Matplotlib documentation for details. You can add styles by adding .mplstyle files to "+matplotlib.get_configdir()+".",
            wraplength = self.width-2*self.cget('padx'),
            justify='left',
        )
        
        self.selectfilter = SelectFilter(
            self.contents,
            left=self.available_styles,
            right=self.current_style,
            selectmode=('extended','dragdrop'),
            labels=("Available styles", "Current style"),
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.place_widgets")
        self.description.pack(side='top',fill='both',expand=True)
        self.selectfilter.pack(side='top',fill='both',expand=True)

    def set_style(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.set_style")

        style = self.selectfilter.right
        self.gui.interactiveplot.set_style(style)

    def apply(self,*args,**kwargs):
        if globals.debug > 1: print("setstyle.apply")

        self.set_style()
        
        style = self.selectfilter.right
        
        self.gui.set_preference("style",style)
        self.gui.save_preferences()
        
        self.close()

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print('setstyle.cancel')

        self.selectfilter.update_values(left=self.available_styles,right=[])
        self.close()

