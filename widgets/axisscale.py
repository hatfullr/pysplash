from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from widgets.radiobutton import RadioButton
from functions.getallchildren import get_all_children
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
        if self._variable and not isinstance(self._variable, tk.StringVar):
            raise TypeError("Keyword argument 'variable' must be of type tk.StringVar. Received type '"+type(self._variable).__name__+"'")
        else: # if self._variable is None
            self._variable = tk.StringVar()
        self._variable.set("linear")

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
            text="^10",
            variable=self._variable,
            value="^10",
            width=0,
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("axisscale.place_widgets")
        self.linear_button.pack(side='left',padx=(2,0),pady=2)
        self.log_button.pack(side='left',pady=2)
        self.pow10_button.pack(side='left',padx=(0,2),pady=2)

    def get_variables(self, *args, **kwargs):
        return [self._variable]

    def disable(self,*args,**kwargs):
        if globals.debug > 1: print("axisscale.disable")
        for child in get_all_children(self):
            self.set_widget_state(child,'disabled')
            
    def enable(self,*args,**kwargs):
        if globals.debug > 1: print("axisscale.enable")
        for child in get_all_children(self):
            self.set_widget_state(child,'normal')
            
    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("axisscale.set_widget_state")
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
    
    def get(self, *args, **kwargs): return self._variable.get() if self._variable else None
    def set(self, value, *args, **kwargs): return self._variable.set(value)
    def trace(self, *args, **kwargs): return self._variable.trace(*args, **kwargs)

    def connect(self, axis, *args, **kwargs):
        if globals.debug > 1: print("axisscale.connect")
        self.axis = axis
