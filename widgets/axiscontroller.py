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
from matplotlib.axis import XAxis, YAxis
import globals
import numpy as np

class AxisController(LabelledFrame,object):
    def __init__(self,master,text,relief='sunken',bd=1,**kwargs):
        if globals.debug > 1: print("axiscontroller.__init__")
        super(AxisController,self).__init__(
            master,
            text,
            relief=relief,
            bd=bd,
            **kwargs
        )

        self.axis = None
        self.limits_cid = None
        
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.previous_limits_low_value = self.limits_low.get()
        self.previous_limits_high_value = self.limits_high.get()

        self.previous_scale = self.scale.get()

        self.scale.trace('w',self.on_scale_changed)

    def get_variables(self,*args,**kwargs):
        return [
            self.value,
            self.scale,
            self.limits_low,
            self.limits_high,
            self.is_adaptive,
        ]
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_variables")
        self.value = tk.StringVar()
        self.scale = tk.StringVar(value='linear')
        self.limits_low = tk.DoubleVar()
        self.limits_high = tk.DoubleVar()
        self.is_adaptive = tk.BooleanVar(value=False)
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.create_widgets")
        self.combobox = ttk.Combobox(
            self,
            state='readonly',
            width=0,
            textvariable=self.value,
        )
        
        self.scale_buttons_frame = tk.Frame(self)
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


        self.limits_frame = tk.Frame(self)
        self.limits_label = tk.Label(self.limits_frame,text="Limits")

        self.limits_entry_low = FloatEntry(
            self.limits_frame,
            width=7,
            textvariable=self.limits_low,
        )
        self.limits_entry_high = FloatEntry(
            self.limits_frame,
            width=7,
            textvariable = self.limits_high,
        )
        self.limits_adaptive_button = SwitchButton(
            self.limits_frame,
            text="Adaptive",
            variable=self.is_adaptive,
            command=self.toggle_adaptive,
        )

    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.place_widgets")
        self.combobox.pack(side='top',fill='x')
        
        self.pow10_button.pack(side='right')
        self.log_button.pack(side='right')
        self.linear_button.pack(side='right')
        self.scale_buttons_frame.pack(side='top',fill='x')

        self.limits_frame.columnconfigure(1,weight=1)
        
        self.limits_adaptive_button.pack(side='right')
        self.limits_entry_high.pack(side='right')
        self.limits_entry_low.pack(side='right')
        self.limits_label.pack(side='right')
        self.limits_frame.pack(side='top',fill='x')
        
    def connect(self,axis):
        if globals.debug > 1: print("axiscontroller.connect")
        self.axis=axis
        if axis is not None:
            self.axis.axes.get_figure().canvas.draw()
        self.update_limits()

    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("controls.set_widget_state")
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
        if globals.debug > 1: print("controls.get_all_children")
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

    def update_limits(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.update_limits")
        if self.axis is None: return
        limits = self.axis.get_view_interval()
        low = self.limits_low.get()
        high = self.limits_high.get()
        if low != round(limits[0],len(str(low))):
            self.limits_low.set(limits[0])
        if high != round(limits[1],len(str(high))):
            self.limits_high.set(limits[1])

        #if self.is_adaptive.get():
        if self.scale != 'log10' and any(limits <= 0):
            self.log_button.configure(state='disabled')
        else:
            self.log_button.configure(state='normal')
        
    def toggle_adaptive(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.toggle_adaptive")
        if self.axis is None: return
        
        if self.is_adaptive.get(): # Turn on adaptive limits
            if(isinstance(self.axis,XAxis)):
                self.limits_cid = self.axis.axes.callbacks.connect("xlim_changed",self.update_limits)
            elif(isinstance(self.axis,YAxis)):
                self.limits_cid = self.axis.axes.callbacks.connect("ylim_changed",self.update_limits)
            else:
                raise ValueError("Unsupported axis type "+type(self.axis))
            
            # Disable the limit entries
            self.limits_entry_low.configure(state='disabled')
            self.limits_entry_high.configure(state='disabled')

            self.previous_limits_low_value = self.limits_low.get()
            self.previous_limits_high_value = self.limits_high.get()
            self.update_limits()
            
        else: # Turn off adaptive limits
            if self.limits_cid is not None:
                self.axis.axes.callbacks.disconnect(self.limits_cid)
                self.limits_cid = None

            self.limits_entry_low.configure(state='normal')
            self.limits_entry_high.configure(state='normal')

            self.limits_low.set(self.previous_limits_low_value)
            self.limits_high.set(self.previous_limits_high_value)

    def on_scale_changed(self,*args,**kwargs):
        if globals.debug > 1: print("axiscontroller.on_scale_changed")

        if not self.is_adaptive.get():
            self.previous_limits_low = self.limits_low.get()
            self.previous_limits_high = self.limits_high.get()
        
        current_scale = self.scale.get()
        if self.previous_scale != current_scale:
            if self.previous_scale == 'linear':
                if current_scale == 'log10':
                    self.limits_low.set(np.log10(self.limits_low.get()))
                    self.limits_high.set(np.log10(self.limits_high.get()))
                else: # Must be ^10
                    self.limits_low.set(10**(self.limits_low.get()))
                    self.limits_high.set(10**(self.limits_high.get()))
            elif self.previous_Scale == 'log10':
                if current_scale == 'linear':
                    self.limits_low.set(10**(self.limits_low.get()))
                    self.limits_high.set(10**(self.limits_high.get()))
                else: # Must be ^10
                    self.limits_low.set(10**(10**(self.limits_low.get())))
                    self.limits_high.set(10**(10**(self.limits_high.get())))
            elif self.previous_scale == '^10':
                if current_scale == 'linear':
                    self.limits_low.set(np.log10(self.limits_low.get()))
                    self.limits_high.set(np.log10(self.limits_high.get()))
                else: # Must be log10
                    self.limits_low.set(np.log10(np.log10(self.limits_low.get())))
                    self.limits_high.set(np.log10(np.log10(self.limits_high.get())))
