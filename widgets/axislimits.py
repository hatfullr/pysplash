from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

from widgets.floatentry import FloatEntry
from widgets.switchbutton import SwitchButton
from widgets.tooltip import ToolTip
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import gui
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisLimits(tk.LabelFrame,object):
    def __init__(self, master, controller, text="Limits", adaptivecommands=(None, None), allowadaptive=True, **kwargs):
        if globals.debug > 1: print("axislimits.__init__")
        super(AxisLimits, self).__init__(master,text=text,**kwargs)
        self.controller = controller
        self.adaptivecommands = adaptivecommands
        self.allowadaptive = allowadaptive
        self.axis = None
        self.cid = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.low.trace(
            'w',
            lambda *args, **kwargs: self.controller.event_generate("<<LimitsChanged>>")
        )
        self.high.trace(
            'w',
            lambda *args, **kwargs: self.controller.event_generate("<<LimitsChanged>>")
        )

        self.connected = False

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.create_variables")
        self.low = DoubleVar(self,0.,'low')
        self.high = DoubleVar(self,0.,'high')
        self.adaptive = BooleanVar(self,False,'adaptive')
        globals.state_variables.append(self.low)
        globals.state_variables.append(self.high)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.create_widgets")

        self.entry_low = FloatEntry(
            self,
            variable=self.low,
        )
        self.entry_high = FloatEntry(
            self,
            variable=self.high,
        )
        self.adaptive_button = SwitchButton(
            self,
            text="A",
            width=2,
            variable=self.adaptive,
            command=(self.adaptive_on, self.adaptive_off),
        )
        ToolTip.createToolTip(self.adaptive_button, "Turn adaptive limits on/off. When turned on, the axis limits will automatically be set such that all data are visible. Disabled while tracking a particle.")

    def get(self, *args, **kwargs):
        return (self.low.get(), self.high.get())
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.place_widgets")

        self.entry_low.pack(side='left',fill='both',expand=True,padx=(2,0),pady=(0,2))
        self.entry_high.pack(side='left',fill='both',expand=True,pady=(0,2))
        if self.allowadaptive: self.adaptive_button.pack(side='left',padx=2,pady=(0,2))

    def configure(self,*args,**kwargs):
        if globals.debug > 1: print("axislimits.configure")
        self.adaptivecommands = kwargs.pop("adaptivecommands",self.adaptivecommands)
        super(AxisLimits,self).configure(*args,**kwargs)
        self.event_generate("<Configure>")

    def config(self,*args,**kwargs):
        if globals.debug > 1: print("axislimits.config")
        return self.configure(*args,**kwargs)
                        
    def connect(self,axis):
        if globals.debug > 1: print("axislimits.connect")
        if axis:
            self.axis=axis
            if isinstance(self.axis, XAxis):
                self.cid = self.axis.axes.callbacks.connect("xlim_changed",self.on_axis_limits_changed)
            elif isinstance(self.axis, YAxis):
                self.cid = self.axis.axes.callbacks.connect("ylim_changed",self.on_axis_limits_changed)
            self.connected = True
            # Update the entry widgets
            self.on_axis_limits_changed()

    def disconnect(self):
        if globals.debug > 1: print("axislimits.disconnect")
        if self.axis and self.cid:
            self.axis.callbacks.disconnect(self.cid)
            self.cid = None
        self.connected = False
            
    def on_axis_limits_changed(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.on_axis_limits_changed")
        if self.axis is None: return
        self.set_limits(self.axis.get_view_interval())

    def set_limits(self, newlimits):
        if globals.debug > 1: print("axislimits.set_limits")
        if None in newlimits:
            raise ValueError("Cannot set limits to None")
        if newlimits[0] is not None: self.low.set(newlimits[0])
        if newlimits[1] is not None: self.high.set(newlimits[1])

    def adaptive_on(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_on")
        if not self.allowadaptive: return
        
        if self.adaptivecommands[0] is not None: self.adaptivecommands[0](*args, **kwargs)

    def adaptive_off(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_off")
        if not self.allowadaptive: return
        
        # Reset the entry boxes to have the current view
        self.on_axis_limits_changed()
        
        if self.adaptivecommands[1] is not None: self.adaptivecommands[1](*args, **kwargs)

    def update_limits(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.update_limits")
        if self.controller.units.entry.get() == "": return
        units = self.controller.units.get()
        if hasattr(self, "previous_units"): # Not the first time
            if abs((self.previous_units-units)/units) > 0.001:
                for limit in [self.low, self.high]:
                    limit.set(limit.get() * self.previous_units / units)
        else: # First time
            for limit in [self.low, self.high]:
                limit.set(limit.get() / units)
        self.previous_units = units
