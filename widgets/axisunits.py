from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
    
from widgets.floatentry import FloatEntry
from functions.getallchildren import get_all_children
from matplotlib.axis import XAxis, YAxis
import globals
import matplotlib.ticker


class AxisUnits(tk.LabelFrame, object):
    def __init__(self, master, text="Units", *args, **kwargs):
        if globals.debug > 1: print("axisunits.__init__")
        super(AxisUnits,self).__init__(master, text=text, **kwargs)
        self.axis = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.previous_units = 1.
        self._major_formatter = None
        self._minor_formatter = None

        self.value.trace("w", self.update_axis_units)

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.create_variables")
        self.value = tk.DoubleVar(value=1)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.create_widgets")
        self.entry = FloatEntry(
            self,
            variable=self.value,
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.place_widgets")
        self.entry.pack(side='right',fill='x',expand=True)

    def get_variables(self, *args, **kwargs):
        return [self.value]

    def connect(self, axis, *args, **kwargs):
        if globals.debug > 1: print("axisunits.connect")
        self.axis = axis
        self._major_formatter = self.axis.get_major_formatter()
        self._minor_formatter = self.axis.get_minor_formatter()
        
    def disconnect(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.disconnect")
        if self.axis:
            self.axis = None
            self._major_formatter = None
            self._minor_formatter = None

    def update_axis_units(self, *args, **kwargs):
        if globals.debug > 1: print("axisunits.update_axis_units")

        if self.value.get() != self.previous_units:
            conversion = self.value.get() / self.previous_units
            if not self._major_formatter or not self._minor_formatter:
                raise ValueError("One of _major_formattor or _minor_formatter are None. Make sure you have connected this AxisUnits to an axis first before calling update_axis_units.")
            self.axis.set_major_formatter(lambda x,pos: self._major_formatter(x*conversion, x))
            self.axis.set_minor_formatter(lambda x,pos: self._minor_formatter(x*conversion, x))

            print(self.axis.get_ticklabels())

            self.previous_units = self.value.get()
