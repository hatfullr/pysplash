from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from widgets.radiobutton import RadioButton
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import globals
import numpy as np

class AxisScale(tk.LabelFrame, object):
    def __init__(self, master, controller, variable=None, text="Scale", *args, **kwargs):
        if globals.debug > 1: print("axisscale.__init__")
        
        super(AxisScale,self).__init__(master,text=text,*args,**kwargs)

        self.axis = None
        self._variable = variable
        self.controller = controller
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        def update_allowed_states(*args,**kwargs):
            self.pow10_allowed.set(
                not self.can_data_overflow_with_pow10(self.controller.data) and
                not self.can_data_overflow_with_pow10(np.array(self.controller.limits.high.get())) and
                not self.can_data_overflow_with_pow10(np.array(self.controller.limits.low.get()))
            )
        
        self.controller.bind("<<DataChanged>>", update_allowed_states, add="+")
        self.controller.bind("<<LimitsChanged>>", update_allowed_states, add="+")

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.create_variables")
        self._variable = StringVar(self, 'linear', '_variable')
        globals.state_variables.append(self._variable)
        self.log_allowed = tk.BooleanVar(value=True)
        self.pow10_allowed = tk.BooleanVar(value=True)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.create_widgets")
        self.linear_button = RadioButton(
            self,
            text="linear",
            variable=self._variable,
            value="linear",
            width=0,
        )
        self.log_button = RadioButton(
            self,
            text="log10",
            variable=self._variable,
            value="log10",
            width=0,
        )
        self.pow10_button = RadioButton(
            self,
            text="10^",
            variable=self._variable,
            value="10^",
            width=0,
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.place_widgets")
        self.linear_button.pack(side='left',padx=(2,0),pady=2)
        self.log_button.pack(side='left',pady=2)
        self.pow10_button.pack(side='left',padx=(0,2),pady=2)

    def get(self, *args, **kwargs): return self._variable.get() if self._variable else None
    def set(self, value, *args, **kwargs): return self._variable.set(value)
    def trace(self, *args, **kwargs): return self._variable.trace(*args, **kwargs)

    def connect(self, axis, *args, **kwargs):
        if globals.debug > 1: print("axisscale.connect")
        self.axis = axis

    # Check if the axis controller's data is able to overflow if it's raised to 10^
    def can_data_overflow_with_pow10(self, data):
        if globals.debug > 1: print('axisscale.can_data_overflow')
        if data is None: return False
        if np.issubdtype(data.dtype, np.floating):
            maxvalue = np.finfo(data.dtype).max
        elif np.issubdtype(data.dtype, np.integer):
            maxvalue = np.iinfo(data.dtype).max
        else:
            raise Exception("unknown dtype '"+str(data.dtype)+"' in data")
        return np.any(data > np.log10(maxvalue))

