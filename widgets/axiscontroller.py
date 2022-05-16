from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

from widgets.labelledframe import LabelledFrame
from widgets.axislimits import AxisLimits
from widgets.axisunits import AxisUnits
from widgets.axisscale import AxisScale
from functions.getallchildren import get_all_children
from widgets.mathentry import MathEntry
from widgets.entry import Entry
from functions.setwidgetsstates import set_widgets_states
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisController(LabelledFrame,object):
    def __init__(self,master,gui,text,relief='sunken',bd=1,allowadaptive=True,usecombobox=True,**kwargs):
        if globals.debug > 1: print("axiscontroller.__init__")
        super(AxisController,self).__init__(
            master,
            text,
            relief=relief,
            bd=bd,
            **kwargs
        )

        self.usecombobox = usecombobox
        
        self.gui = gui

        self.axis = None
        self.cid = None
        self.allowadaptive=allowadaptive
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.previous_scale = self.scale.get()
        self.previous_units = self.units.value.get()
        
        self.scale.trace('w',self.on_scale_changed)
        self.limits.low.trace('w',self.update_scale_buttons)
        self.limits.high.trace('w',self.update_scale_buttons)
        #self.units.value.trace('w',self.update_limits)

        if self.usecombobox:
            self.combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected, add='+')
        self.previous_value = None
        

    def get_variables(self,*args,**kwargs):
        return [
            self.value,
            self.scale,
            self.label,
        ]
    
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_variables")
        self.value = tk.StringVar(value='None')
        self.scale = tk.StringVar(value='linear')
        self.label = tk.StringVar()
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_widgets")
        if self.usecombobox:
            self.combobox = ttk.Combobox(
                self,
                state='readonly',
                width=0,
                values=[self.value.get()],
                textvariable=self.value,
            )
        else:
            self.value.set("")
            self.entry = MathEntry(
                self,
                self.gui,
                textvariable=self.value,
            )

        self.label_frame = tk.LabelFrame(self,text="Label")
        self.label_entry = Entry(
            self.label_frame,
            textvariable=self.label,
        )
        
        self.limits = AxisLimits(self,adaptivecommands=(self.set_adaptive_limits,None),allowadaptive=self.allowadaptive)
        self.units_and_scale_frame = tk.Frame(self)
        self.units = AxisUnits(self.units_and_scale_frame, self)
        self.scale = AxisScale(self.units_and_scale_frame)
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.place_widgets")
        if self.usecombobox: self.combobox.pack(side='top',fill='both')
        else: self.entry.pack(side='top',fill='both')

        self.label_entry.pack(fill='both',expand=True,padx=2,pady=(0,2))
        self.label_frame.pack(side='top',fill='both',expand=True)

        self.limits.pack(side='top',fill='x')

        self.units.pack(side='left',fill='both',expand=True,padx=(0,5))
        self.scale.pack(side='left')
        self.units_and_scale_frame.pack(side='top',fill='x',expand=True)

    def on_combobox_selected(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.on_combobox_selected")
        # Check for any <= 0 values in the data. If there are any, then if
        # the user is in log10 scale mode, we need to switch them out of it
        if self.usecombobox:
            if self.value.get() in self.gui.data['data'].keys():
                if any(self.gui.get_display_data(self.value.get(), scaled=False) <= 0):
                    if self.scale.get() == "log10":
                        self.scale.linear_button.invoke()
                        self.on_scale_changed()
        #else: # If all values in the data are positive and non-zero
        self.set_adaptive_limits()
        
        self.previous_value = self.value.get()
        
    def connect(self,axis,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.connect")
        if axis is not None:
            self.axis = axis
            self.limits.connect(self.axis)
            self.scale.connect(self.axis)
            self.cid = self.axis.get_figure().canvas.mpl_connect("draw_event", self.update_labels)
    
    def disconnect(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.disconnect")
        self.limits.disconnect()
        self.scale.disconnect()
        if self.axis and self.cid:
            self.axis.get_figure().canvas.mpl_disconnect(self.cid)
            self.cid = None
     
    
        
    def disable(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.disable")
        set_widgets_states(get_all_children(self), 'disabled')

    def enable(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.enable")
        set_widgets_states(get_all_children(self), 'normal')
    

    def update_labels(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.update_labels")
        if self.axis.get_label_text() != self.label.get():
            parent_ax = self.axis.axes
            if isinstance(self.axis, XAxis):
                parent_ax.set_xlabel(self.label.get())
            elif isinstance(self.axis, YAxis):
                parent_ax.set_ylabel(self.label.get())

    def update_scale_buttons(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.update_scale_buttons")
        
        # Never allow log10 when <= 0 data is present
        #if self.gui.data is not None:
        #    if self.value.get() not in self.gui.data['data'].keys(): return
        #
        #    data = self.gui.get_display_data(self.value.get(), scaled=False)
        #    if np.any(data <= 0):
        #        self.scale.log_button.configure(state='disabled')
        #        return
        
        # Only do this if we are not using adaptive limits
        #if not self.limits.adaptive.get():
        limits = [self.limits.low.get(), self.limits.high.get()]
        
        # Allow negative values if we are in the log10 scale, but if we are in
        # any other scale then disable the log10 button
        if self.scale.get() != 'log10' and any([l <= 0. for l in limits]):
            self.scale.log_button.state(['disabled'])
        else:
            self.scale.log_button.state(['!disabled'])
            
    def on_scale_changed(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.on_scale_changed")

        current_scale = self.scale.get()
        if self.previous_scale != current_scale:
            # First reset the units so that things don't get mucked up
            self.units.reset()

            low = self.limits.low.get()
            high = self.limits.high.get()
            
            if self.previous_scale == 'linear':
                if current_scale == 'log10':
                    self.limits.low.set(np.log10(low))
                    self.limits.high.set(np.log10(high))
                else: # Must be ^10
                    self.limits.low.set(10**(low))
                    self.limits.high.set(10**(high))
            elif self.previous_scale == 'log10':
                # If we are switching off of log10 then it's possible that the limits
                # could be nan. If this is the case, then we need to recalculate that
                # bound if possible
                #re_low = None
                #re_high = None
                #if np.isnan(low) and np.isnan(high): re_low, re_high = self.recalculate_limit(which='both')
                #elif np.isnan(low): re_low = self.recalculate_limit(which='low')
                #elif np.isnan(high): re_high = self.recalculate_limit(which='high')
                if current_scale == 'linear':
                    self.limits.low.set(10**low)
                    self.limits.high.set(10**high)
                    #if re_low: self.limits.low.set(re_low)
                    #else: self.limits.low.set(10**(low))
                    #if re_high: self.limits.high.set(re_high)
                    #else: self.limits.high.set(10**(high))
                else: # Must be ^10
                    self.limits.low.set(10**(10**low))
                    self.limits.high.set(10**(10**high))
                    #if re_low: self.limits.low.set(10**re_low)
                    #else: self.limits.low.set(10**(10**(low)))
                    #if re_high: self.limits.high.set(10**re_high)
                    #else: self.limits.high.set(10**(10**(high)))
            elif self.previous_scale == '^10':
                if current_scale == 'linear':
                    self.limits.low.set(np.log10(low))
                    self.limits.high.set(np.log10(high))
                else: # Must be log10
                    self.limits.low.set(np.log10(np.log10(low)))
                    self.limits.high.set(np.log10(np.log10(high)))
                    
            self.previous_scale = current_scale
    
    def update_limits(self, *args, **kwargs):
        if globals.debug > 1: print('axiscontroller.update_limits')
        units = self.units.value.get()
        if abs((self.previous_units-units)/units) > 0.001:
            for limit in [self.limits.low, self.limits.high]:
                limit.set(limit.get() * self.previous_units / units)
            self.previous_units = units


    def set_adaptive_limits(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.set_adaptive_limits")
        # Set the limit entries to be the data's true, total limits
        if self.axis is not None:
            # Check if this axis is the colorbar
            if self.axis._axes is self.gui.interactiveplot.colorbar.cax:
                newlim = self.gui.interactiveplot.colorbar.calculate_limits()
                # This axis is either the x or y axes of the main plot (not the colorbar)
            elif isinstance(self.axis, XAxis):
                newlim, dummy = self.gui.interactiveplot.calculate_xylim(which='xlim')
            elif isinstance(self.axis, YAxis):
                dummy, newlim = self.gui.interactiveplot.calculate_xylim(which='ylim')
            
            if None not in newlim:
                # Apply the current scale to the new limits
                if self.scale.get() == 'log10': newlim = np.log10(newlim)
                elif self.scale.get() == '^10': newlim = 10.**newlim
                self.limits.set_limits(newlim)
