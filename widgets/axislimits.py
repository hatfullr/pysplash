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
from functions.getallchildren import get_all_children
import gui
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisLimits(tk.LabelFrame,object):
    def __init__(self, master, text="Limits", allowadaptive=True, **kwargs):
        if globals.debug > 1: print("axislimits.__init__")
        super(AxisLimits, self).__init__(master,text=text,**kwargs)

        self.allowadaptive = allowadaptive
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
        self.low = tk.DoubleVar(value=0.)
        self.high = tk.DoubleVar(value=0.)
        self.adaptive = tk.BooleanVar(value=False)

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
        ToolTip.createToolTip(self.adaptive_button, "Turn adaptive limits on/off. When turned on, the axis limits will automatically be set such that all data are visible.")
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.place_widgets")

        self.entry_low.pack(side='left',fill='both',expand=True,padx=(2,0),pady=(0,2))
        self.entry_high.pack(side='left',fill='both',expand=True,pady=(0,2))
        if self.allowadaptive: self.adaptive_button.pack(side='left',padx=2,pady=(0,2))

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
        if globals.debug > 1: print("axislimits.disable")
        for child in get_all_children(self):
            self.set_widget_state(child,'disabled')
    def enable(self,*args,**kwargs):
        if globals.debug > 1: print("axislimits.enable")
        for child in get_all_children(self):
            self.set_widget_state(child,'normal')
                        
    def connect(self,axis):
        if globals.debug > 1: print("axislimits.connect")
        if axis:
            self.axis=axis
            if isinstance(self.axis, XAxis):
                self.cid = self.axis.callbacks.connect("xlim_changed",self.on_axis_limits_changed)
            elif isinstance(self.axis, YAxis):
                self.cid = self.axis.callbacks.connect("ylim_changed",self.on_axis_limits_changed)
            
            # Update the entry widgets
            self.on_axis_limits_changed()

    def disconnect(self):
        if globals.debug > 1: print("axislimits.disconnect")
        if self.axis and self.cid:
            self.axis.callbacks.disconnect(self.cid)
            self.cid = None
            
    def on_axis_limits_changed(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.on_axis_limits_changed")
        if self.axis is None: return
        self.set_limits(self.axis.get_view_interval())

    def set_limits(self, newlimits):
        if globals.debug > 1: print("axislimits.set_limits")
        self.low.set(newlimits[0])
        self.high.set(newlimits[1])
        #low = self.low.get()
        #high = self.high.get()
        #if low != round(limits[0],len(str(low))):
        #    self.low.set(limits[0])
        #if high != round(limits[1],len(str(high))):
        #    self.high.set(limits[1])

    def adaptive_on(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_on")
        if not self.allowadaptive: return
        
        self.adaptive.set(True)
        
        # Disable the limit entries
        self.entry_low.configure(state='disabled')
        self.entry_high.configure(state='disabled')

        
        # Set the limit entries to be the data's true, total limits
        if self.axis:
            # Try to locate the GUI widget
            for child in self.winfo_toplevel().winfo_children():
                if isinstance(child, gui.gui.GUI):
                    # Check if this axis is the colorbar
                    if self.axis._axes is child.interactiveplot.colorbar.cax:
                        newlim = child.interactiveplot.colorbar.calculate_limits()
                    # This axis is either the x or y axes of the main plot (not the colorbar)
                    else:
                        if isinstance(self.axis, XAxis):
                            newlim, dummy = child.interactiveplot.calculate_xylim(which='xlim')
                        elif isinstance(self.axis, YAxis):
                            dummy, newlim = child.interactiveplot.calculate_xylim(which='ylim')
                            
                    if None not in newlim: self.set_limits(newlim)
                    break
        
            

    def adaptive_off(self, *args, **kwargs):
        if globals.debug > 1: print("axislimits.adaptive_off")
        if not self.allowadaptive: return
        
        self.adaptive.set(False)
        
        # Enable the limit entries
        self.entry_low.configure(state='normal')
        self.entry_high.configure(state='normal')
