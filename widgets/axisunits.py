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
    def __init__(self, master, axis_controller, text="Units", *args, **kwargs):
        if globals.debug > 1: print("axisunits.__init__")
        self.axis_controller = axis_controller
        super(AxisUnits,self).__init__(master, text=text, **kwargs)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.value.trace('w',self.axis_controller.update_limits)
        if self.axis_controller.usecombobox:
            self.axis_controller.bind("<<ComboboxSelected>>", self.on_axis_controller_combobox_selected)

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

    def reset(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.reset")
        self.value.set(1.)

    def on_axis_controller_combobox_selected(self,*args,**kwargs):
        if globals.debug > 1: print('axisunits.on_axis_controller_combobox_selected')
        if self.axis_controller.usecombobox:
            if self.axis_controller.previous_value != self.axis_controller.value.get():
                self.reset()
