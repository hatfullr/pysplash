from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk

from widgets.labelledframe import LabelledFrame
from widgets.floatentry import FloatEntry
from widgets.switchbutton import SwitchButton
from widgets.axislimits import AxisLimits
import gui
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisController(LabelledFrame,object):
    def __init__(self,master,text,relief='sunken',bd=1,allowadaptive=True,**kwargs):
        if globals.debug > 1: print("axiscontroller.__init__")
        super(AxisController,self).__init__(
            master,
            text,
            relief=relief,
            bd=bd,
            **kwargs
        )

        self.axis = None
        self.allowadaptive=allowadaptive
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.previous_scale = self.scale.get()
        
        self.scale.trace('w',self.on_scale_changed)
        self.limits.low.trace('w',self.update_scale_buttons)
        self.limits.high.trace('w',self.update_scale_buttons)

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
        self.combobox = ttk.Combobox(
            self,
            state='readonly',
            width=0,
            values=[self.value.get()],
            textvariable=self.value,
        )

        self.label_and_scale_frame = tk.Frame(self)

        self.label_frame = tk.Frame(self.label_and_scale_frame)
        self.label_label = tk.Label(self.label_frame,text="Label")
        self.label_entry = tk.Entry(
            self.label_frame,
            textvariable=self.label,
            width=11,
        )
        
        self.scale_buttons_frame = tk.Frame(self.label_and_scale_frame)
        self.linear_button = tk.Radiobutton(
            self.scale_buttons_frame,
            text="linear",
            variable=self.scale,
            indicatoron=False,
            value="linear",
            padx=5,
            pady=5,
        )
        self.log_button = tk.Radiobutton(
            self.scale_buttons_frame,
            text="log10",
            variable=self.scale,
            indicatoron=False,
            value="log10",
            padx=5,
            pady=5,
        )
        self.pow10_button = tk.Radiobutton(
            self.scale_buttons_frame,
            text="^10",
            variable=self.scale,
            indicatoron=False,
            value="^10",
            padx=5,
            pady=5,
        )


        self.limits = AxisLimits(self,allowadaptive=self.allowadaptive)
        
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.place_widgets")
        self.combobox.pack(side='top',fill='x')

        self.label_entry.pack(side='right')
        self.label_label.pack(side='right')
        self.label_frame.pack(side='left')
        
        self.pow10_button.pack(side='right')
        self.log_button.pack(side='right')
        self.linear_button.pack(side='right')
        self.scale_buttons_frame.pack(side='right',fill='x')
        
        self.label_and_scale_frame.pack(side='top',fill='x')

        self.limits.pack(side='top',fill='x',padx=2)
        
    def connect(self,axis):
        if globals.debug > 1: print("axiscontroller.connect")
        if axis is not None:
            self.axis = axis
            self.limits.connect(self.axis)
            self.axis.get_figure().canvas.mpl_connect("draw_event", self.update_labels)
        
    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("axiscontroller.set_widget_state")
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

    def get_all_children(self, finList=[], wid=None):
        if globals.debug > 1: print("axiscontroller.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
        
    def disable(self,*args,**kwargs):
        for child in self.get_all_children():
            self.set_widget_state(child,'disabled')
    def enable(self,*args,**kwargs):
        for child in self.get_all_children():
            self.set_widget_state(child,'normal')

    def update_scale_buttons(self, *args, **kwargs):
        if globals.debug > 1: print("axiscontroller.update_scale_buttons")

        # Only do this if we are not using adaptive limits
        if not self.limits.adaptive.get():
        
            limits = [self.limits.low.get(), self.limits.high.get()]
            # Allow negative values if we are in the log10 scale, but if we are in
            # any other scale then disable the log10 button
            if self.scale.get() != 'log10' and any([l <= 0 for l in limits]):
                self.log_button.configure(state='disabled')
            else:
                self.log_button.configure(state='normal')

    def update_labels(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.update_labels")
        
        if self.axis.get_label_text() != self.label.get():
            parent_ax = self.axis.axes
            if isinstance(self.axis, XAxis):
                parent_ax.set_xlabel(self.label.get())
            elif isinstance(self.axis, YAxis):
                parent_ax.set_ylabel(self.label.get())
    
    def on_scale_changed(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.on_scale_changed")

        low = self.limits.low.get()
        high = self.limits.high.get()

        current_scale = self.scale.get()
        if self.previous_scale != current_scale:
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
