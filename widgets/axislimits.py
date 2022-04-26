from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

from widgets.floatentry import FloatEntry
from widgets.switchbutton import SwitchButton
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisLimits(tk.LabelFrame,object):
    def __init__(self, master, text="Limits", **kwargs):

        super(AxisLimits, self).__init__(master,text=text,**kwargs)

        self.axis = None
        self.cid = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

    def get_variables(self, *args, **kwargs):
        return [
            self.low,
            self.high,
            self.adaptive,
        ]

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.create_variables")
        self.low = tk.DoubleVar()
        self.high = tk.DoubleVar()
        self.adaptive = tk.BooleanVar(value=False)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.create_widgets")

        self.entry_low = FloatEntry(
            self,
            textvariable=self.low,
        )
        self.entry_high = FloatEntry(
            self,
            textvariable=self.high,
        )
        self.adaptive_button = SwitchButton(
            self,
            text="Adaptive",
            variable=self.adaptive,
            command=(self.adaptive_on, self.adaptive_off),
        )
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.place_widgets")

        self.entry_low.pack(side='left',fill='x',expand=True)
        self.entry_high.pack(side='left',fill='x',expand=True)
        self.adaptive_button.pack(side='left')

    def get_all_children(self, finList=[], wid=None):
        if globals.debug > 1: print("axislimits.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList

    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("axislimits.set_widget_state")
        if not isinstance(widgets,(list,tuple,np.ndarray)): widgets = [widgets]
        for widget in widgets:
            if 'state' in widget.configure():
                if isinstance(widget,tk.Label): continue
                current_state = widget.cget('state')
                if current_state != state:
                    if isinstance(widget,ttk.Combobox):
                        if state == 'normal': widget.configure(state='readonly')
                    else:
                        widget.configure(state=state)

    def disable(self,*args,**kwargs):
        for child in self.get_all_children():
            self.set_widget_state(child,'disabled')
    def enable(self,*args,**kwargs):
        for child in self.get_all_children():
            self.set_widget_state(child,'normal')
                        
    def connect(self,axis):
        if globals.debug > 1: print("axislimits.connect")
        if axis:
            self.axis=axis
            if isinstance(axis, XAxis):
                self.axis.callbacks.connect("xlim_changed",self.on_axis_limits_changed)
            elif isinstance(axis, YAxis):
                self.axis.callbacks.connect("ylim_changed",self.on_axis_limits_changed)
            else:
                raise ValueError("Unsupported axis type "+type(self.axis))
            
            # Update the entry widgets
            self.on_axis_limits_changed()

    def disconnect(self):
        if globals.debug > 1: print("axislimits.disconnect")
        if self.axis and self.cid:
            self.axis.axes.callbacks.disconnect(self.cid)
            self.cid = None
            
    def on_axis_limits_changed(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.on_axis_limits_changed")
        if self.axis is None: return
        
        limits = self.axis.get_view_interval()
        self.low.set(limits[0])
        self.high.set(limits[1])

        #low = self.low.get()
        #high = self.high.get()
        #if low != round(limits[0],len(str(low))):
        #    self.low.set(limits[0])
        #if high != round(limits[1],len(str(high))):
        #    self.high.set(limits[1])

    def adaptive_on(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_on")

        # If we receive arguments then it's the user who pressed the button to call this event.
        # Otherwise, it is an internal call and so we should simulate a button press
        if not args:
            self.adaptive_button.command()
        
        # Disable the limit entries
        self.entry_low.configure(state='disabled')
        self.entry_high.configure(state='disabled')
        
        self.connect(self.axis)

    def adaptive_off(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_off")

        # If we receive arguments then it's the user who pressed the button to call this event.
        # Otherwise, it is an internal call and so we should simulate a button press
        if not args:
            self.adaptive_button.command()
        
        # Enable the limit entries
        self.entry_low.configure(state='normal')
        self.entry_high.configure(state='normal')

        self.disconnect()
