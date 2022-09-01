from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from widgets.radiobutton import RadioButton
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import globals

class AxisScale(tk.LabelFrame, object):
    def __init__(self, master, variable=None, text="Scale", *args, **kwargs):
        if globals.debug > 1: print("axisscale.__init__")
        
        super(AxisScale,self).__init__(master,text=text,*args,**kwargs)

        self.axis = None
        self._variable = variable
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.create_variables")
        if self._variable and not isinstance(self._variable, StringVar):
            raise TypeError("Keyword argument 'variable' must be of type StringVar. Received type '"+type(self._variable).__name__+"'")
        else: # if self._variable is None
            self._variable = StringVar(self, 'linear', '_variable')
        #self._variable.set("linear")

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.create_widgets")
        self.linear_button = RadioButton(
            self,
            text="linear",
            variable=self._variable,
            value="linear",
            width=0,
            state='disabled',
        )
        self.log_button = RadioButton(
            self,
            text="log10",
            variable=self._variable,
            value="log10",
            width=0,
            state='disabled',
        )
        self.pow10_button = RadioButton(
            self,
            text="^10",
            variable=self._variable,
            value="^10",
            width=0,
            state='disabled',
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
        # data is what we have control of
        self.axis = axis

    def disable(self, *args, **kwargs):
        if globals.debug > 1: print('axisscale.disable')
        self.linear_button.configure(state='disabled')
        self.log_button.configure(state='disabled')
        self.pow10_button.configure(state='disabled')

    def enable(self, *args, **kwargs):
        if globals.debug > 1: print('axisscale.enable')
        self.linear_button.configure(state='normal')
        self.log_button.configure(state='normal')
        self.pow10_button.configure(state='normal')
