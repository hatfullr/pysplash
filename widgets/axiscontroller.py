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
from widgets.mathcombobox import MathCombobox
from matplotlib.axis import XAxis, YAxis
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
import globals
import numpy as np

class AxisController(LabelledFrame,object):
    min_log_default = 1.e-6
    def __init__(self,master,gui,text,relief='sunken',bd=1,allowadaptive=True,**kwargs):
        if globals.debug > 1: print("axiscontroller.__init__")
        super(AxisController,self).__init__(
            master,
            text,
            relief=relief,
            bd=bd,
            **kwargs
        )

        self.name = text

        
        self.gui = gui

        self.axis = None
        self.cid = None
        self.allowadaptive=allowadaptive
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.previous_value = self.value.get()
        self.previous_scale = self.scale.get()
        self.previous_units = self.units.value.get()

        #self.value.trace('w', self.set_widgets_states)
        self.scale.trace('w', self.on_scale_changed)
        self.label.trace('w', self.update_label)
        
        self.combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected, add='+')

        #self.combobox.bind("<Configure>", self.set_widgets_states, add="+")

        self._data = None
        self.stale = False
        self._physical_units = None
        self._display_units = None
        self._setting_label = True
        self._pow10_bid = None

    @property
    def data(self):
        if self.gui.data is not None and not self.gui.data.is_image:
            if self.stale:
                self._data, self._physical_units, self._display_units = self.combobox.get()
                if self._data is not None:
                    # Apply the scaling to the resulting data
                    if not self.is_colorbar:
                        scale = self.scale.get()
                        if scale == 'log10': self._data = np.log10(self._data)
                        elif scale == '10^':
                            if self.scale.can_data_overflow_with_pow10(self._data):
                                self.scale.set('linear')
                            else: self._data = 10.**self._data

                    self.stale = False
                    self.event_generate("<<DataChanged>>")
        return self._data
    @property
    def physical_units(self):
        if self.stale: self.data
        return self._physical_units
    @property
    def display_units(self):
        if self.stale: self.data
        return self._display_units

    @property
    def is_colorbar(self):
        return self.axis is not None and self.axis._axes is self.gui.interactiveplot.colorbar.cax

    
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_variables")
        self.value = StringVar(self, None, 'value')
        self.label = StringVar(self, None, 'label')
        globals.state_variables.append(self.value)
        globals.state_variables.append(self.label)
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_widgets")
        self.combobox = MathCombobox(
            self,
            self.gui,
            width=0,
            values=[self.value.get()],
            textvariable=self.value,
            where='top',
        )

        self.label_frame = tk.LabelFrame(self,text="Label")
        self.label_entry = Entry(
            self.label_frame,
            textvariable=self.label,
        )
        
        self.limits = AxisLimits(self,self,adaptivecommands=(self.set_adaptive_limits,None),allowadaptive=self.allowadaptive)
        self.units_and_scale_frame = tk.Frame(self)
        self.units = AxisUnits(self.units_and_scale_frame, self)
        self.scale = AxisScale(self.units_and_scale_frame, self)
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.place_widgets")
        self.combobox.pack(side='top',fill='both')

        self.label_entry.pack(fill='both',expand=True,padx=2,pady=(0,2))
        self.label_frame.pack(side='top',fill='both',expand=True)

        self.limits.pack(side='top',fill='x')

        self.units.pack(side='left',fill='both',expand=True,padx=(0,5))
        self.scale.pack(side='left')
        self.units_and_scale_frame.pack(side='top',fill='x',expand=True)

    # This gets called whenever the combobox entry has been changed
    def on_combobox_selected(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.on_combobox_selected")
        # Check for any <= 0 values in the data. If there are any, then if
        # the user is in log10 scale mode, we need to switch them out of it
        value = self.value.get()
        if value != self.previous_value:
            
            #self.set_widgets_states()
            self.gui.time_mode.set(any([controller.value.get() in ['t','time','Time'] for controller in self.gui.controls.axis_controllers.values()]))
            
            if self.gui.data is not None:
                # When the user selects time as an axis, we need to change global behaviors
                
                if not self.gui.time_mode.get():
                    if value in self.gui.data['data'].keys():
                        if np.any(self.gui.get_display_data(value, raw=True) <= 0):
                            if self.scale.get() == "log10":
                                self.scale.linear_button.invoke()
                                self.on_scale_changed()

                    self.set_adaptive_limits()
                    
                    if self.label.get().strip() in ['',self.previous_value] or self.previous_value is None: self.label.set(value)

            if self.previous_value != value: self.stale = True
            self.previous_value = value
        
    def connect(self,axis,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.connect")
        if axis is not None:
            self.axis = axis
            self.limits.connect(self.axis)
            self.scale.connect(self.axis)
            self.update_label()
    
    def disconnect(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.disconnect")
        self.limits.disconnect()
        self.scale.disconnect()
    
    def update_label(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.update_label")

        label = self.label.get()
        if self._setting_label:
            if label in ['None',None]: label = ''
            self.label.set(label)
            self._setting_label = False
        
        if self.axis:
            if self.axis.get_label_text() != label:
                parent_ax = self.axis.axes
                if isinstance(self.axis, XAxis): parent_ax.set_xlabel(label)
                elif isinstance(self.axis, YAxis): parent_ax.set_ylabel(label)
                else:
                    raise Exception("unknown axis type '"+type(self.axis).__name__+"'")
        self._setting_label = True

    def on_scale_changed(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.on_scale_changed")
        
        current_scale = self.scale.get()
        if self.previous_scale != current_scale:
            # First reset the units so that things don't get mucked up
            self.units.reset()

            self.stale = True
            
            # Recalculate the axis limits if we are in adaptive mode
            if self.limits.adaptive.get():
                self.set_adaptive_limits()
            # Otherwise, try to calculate the new limits given the old
            else:
                low = self.limits.low.get()
                high = self.limits.high.get()

                if current_scale == 'log10':
                    low = max(low, AxisController.min_log_default)
                if self.previous_scale == 'linear':
                    if current_scale == 'log10':
                        self.limits.low.set(np.log10(low))
                        self.limits.high.set(np.log10(high))
                    else: # Must be 10^
                        self.limits.low.set(10**(low))
                        self.limits.high.set(10**(high))
                elif self.previous_scale == 'log10':
                    if current_scale == 'linear':
                        self.limits.low.set(10**low)
                        self.limits.high.set(10**high)
                    else: # Must be 10^
                        self.limits.low.set(10**(10**low))
                        self.limits.high.set(10**(10**high))
                elif self.previous_scale == '10^':
                    if current_scale == 'linear':
                        self.limits.low.set(np.log10(low))
                        self.limits.high.set(np.log10(high))
                    else: # Must be log10
                        self.limits.low.set(np.log10(np.log10(low)))
                        self.limits.high.set(np.log10(np.log10(high)))

            self.update_label_log_tag()
            
            self.previous_scale = current_scale
            # Let CustomColorbar handle this
            if self.is_colorbar:
                self.event_generate("<<OnScaleChanged>>")
                #return

    def update_label_log_tag(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.update_label_log_tag")
        current_scale = self.scale.get()
        label = self.label.get()
        if label in ["", " "]: return
        newlabel = label
        loglabels = ["log ", "$\\log_{10}"]
        if current_scale != 'log10':
            for loglabel in loglabels:
                if label[:len(loglabel)] == loglabel:
                    newlabel = newlabel[len(loglabel):]
                    break
            if newlabel[-1] == "$" and newlabel[0] != "$": newlabel = "$"+newlabel
        else:
            for loglabel in loglabels:
                if loglabel in newlabel: break
            else:
                if newlabel[0] == "$": newlabel = "$\\log_{10}"+newlabel[1:]
                else: newlabel = "log "+newlabel
        if newlabel != label: self.label.set(newlabel)

    def set_adaptive_limits(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.set_adaptive_limits")

        if self.gui.data is not None and self.gui.data.is_image:
            if self.is_colorbar:
                limits = np.array([np.nanmin(self.gui.data['image']), np.nanmax(self.gui.data['image'])])
            else:
                if isinstance(self.axis, XAxis):
                    limits = np.array(self.gui.data['extent'][:2])
                elif isinstance(self.axis, YAxis):
                    limits = np.array(self.gui.data['extent'][2:])
                else: raise Exception("This should never happen")
            limits /= self.units.get()
            self.limits.set_limits(limits)
        else:
            # Set the limit entries to be the data's true, total limits
            if self.axis is not None:
                newlim = [None, None]
                # Check if this axis is the colorbar
                if self.is_colorbar:
                    # Take a guess at what the limits of the colorbar should be
                    if self.data is None: return
                    idx = np.isfinite(self.data)
                    newlim = [np.nanmin(self.data[idx]), np.nanmax(self.data[idx])]
                    #pass
                    #pass # Let CustomColorbar handle this
                    #newlim = self.gui.interactiveplot.colorbar.calculate_limits()
                    #if self.scale.get() == 'log10': newlim = np.log10(np.array(newlim))
                    #elif self.scale.get() == '10^': newlim = 10**np.array(newlim)
                    # This axis is either the x or y axes of the main plot (not the colorbar)
                elif isinstance(self.axis, XAxis):
                    newlim, dummy = self.gui.interactiveplot.calculate_xylim(which='xlim')
                elif isinstance(self.axis, YAxis):
                    dummy, newlim = self.gui.interactiveplot.calculate_xylim(which='ylim')

                if None not in newlim:
                    self.limits.set_limits(newlim)

