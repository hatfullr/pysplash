from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

class AxisUnits(tk.LabelFrame, object):
    def __init__(self, master, text="Units", **kwargs):
        if globals.debug > 1: print("axisunits.__init__")
        super(AxisUnits,self).__init__(master, text=text, **kwargs)
        self.axis = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.create_variables")

    def create_widgets(self, *args, **kwargs):

    def place_widgets(self, *args, **kwargs):

    def get_variables(self, *args, **kwargs):
        
