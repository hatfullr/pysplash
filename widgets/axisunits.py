from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
    
from widgets.floatentry import FloatEntry
from functions.getallchildren import get_all_children
from matplotlib.axis import XAxis, YAxis
import matplotlib.image
import copy
import globals

class AxisUnits(tk.LabelFrame, object):
    def __init__(self, master, text="Units", *args, **kwargs):
        if globals.debug > 1: print("axisunits.__init__")
        super(AxisUnits,self).__init__(master, text=text, **kwargs)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.create_variables")
        self.value = tk.DoubleVar(value=1)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.create_widgets")
        self.entry = FloatEntry(
            self,
            variable=self.value,
            disallowed_values=[0,0.,-0,-0.],
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.place_widgets")
        self.entry.pack(side='right',fill='both',expand=True,padx=2,pady=(0,2))

    def get_variables(self, *args, **kwargs):
        return [self.value]

