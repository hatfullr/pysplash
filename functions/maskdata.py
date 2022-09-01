from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.button import Button
from widgets.popupwindow import PopupWindow
from widgets.saveablecodetext import SaveableCodeText
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import os
import globals

class MaskData(PopupWindow, object):
    path = os.path.join(globals.profile_path,"data")
    
    def __init__(self, gui):
        if globals.debug > 1: print("maskdata.__init__")

        # Setup the window
        super(MaskData, self).__init__(
            gui,
            title="Mask data",
            oktext="Apply",
            canceltext="Close",
            okcommand=self.apply,
            name="maskdata",
        )
        
        self.gui = gui

        self.create_variables()
        self.create_widgets()
        self.place_widgets()


    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("maskdata.create_variables")

    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("maskdata.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Enter any arbitrary Python code you wish below to apply a mask to your data. You can reference data variables by their names shown in the dropdown selection box of the axis controllers, such as \"x\", \"y\", \"z\", etc. Your code must terminate with the line \"result = <your result>\" where \"<your result>\" represents a 1D boolean or integer array with the same length as the data arrays. You can save your code by giving it a name and clicking \"Save\".",
            wraplength = self.width - 2*self.cget('padx'),
        )
        
        self.codetext = SaveableCodeText(self.contents,MaskData.path)

        self.clear_button = Button(
            self.buttons_frame,
            text='Clear',
            command=self.clear,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("maskdata.place_widgets")
        self.description.pack(side='top',fill='both',expand=True)
        self.codetext.pack(side='top',fill='both',expand=True)
        self.clear_button.pack(side='left')

    def apply(self,*args,**kwargs):
        if globals.debug > 1: print("maskdata.apply")
        result = self.get_data()
        self.gui.data.mask(result)
        self.gui.interactiveplot.reset()
        self.gui.interactiveplot.update()

    def clear(self,*args,**kwargs):
        if globals.debug > 1: print("maskdata.clear")
        self.gui.data.clear_mask()
        self.gui.interactiveplot.reset()
        self.gui.interactiveplot.update()
    
    def get_data(self, *args, **kwargs):
        if globals.debug > 1: print("maskdata.get_data")
        text = self.codetext.get('1.0','end-1c')
        
        data = self.gui.data['data']
        variables = {key:self.gui.get_display_data(key,scaled=False) for key in data.keys()}
        
        imp = "\n".join(globals.exec_imports)+"\n"
        if "result =" not in text and "result=" not in text:
            text = imp+"result = "+text
        else:
            text = imp+text

        # We feed in the unscaled variables only
        loc = {}
        exec(text, variables, loc)
        result = loc['result']
        return result
