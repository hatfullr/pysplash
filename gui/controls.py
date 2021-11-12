from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk
from collections import OrderedDict
from widgets.integerentry import IntegerEntry
from widgets.labelledframe import LabelledFrame
from widgets.floatentry import FloatEntry
from widgets.switchbutton import SwitchButton
import numpy as np
import globals

class Controls(tk.Frame,object):
    def __init__(self,gui,*args,**kwargs):
        if globals.debug > 1: print("controls.__init__")
        self.gui = gui
        super(Controls,self).__init__(self.gui,*args,**kwargs)
        
        style = ttk.Style()
        style.map('TCombobox', fieldbackground=[('readonly','white')])
        style.map('TCombobox', selectbackground=[('readonly', 'white')])
        style.map('TCombobox', selectforeground=[('readonly', 'black')])
        style.map('TCombobox', fieldbackground=[('disabled',self.gui["bg"])])
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()

        self.caxis_combobox.bind("<<ComboboxSelected>>",self.change_colorbar_type)
        self.saved_state = None
        self.previous_state = None
        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")
        self.x = tk.StringVar()
        self.y = tk.StringVar()
        self.c = tk.StringVar(value='None')
        self.xaxis_scale = tk.StringVar(value="linear")
        self.yaxis_scale = tk.StringVar(value="linear")
        self.caxis_scale = tk.StringVar(value="linear")
        self.point_size = tk.IntVar(value=1)

        self.rotation_x = tk.DoubleVar(value=0)
        self.rotation_y = tk.DoubleVar(value=0)
        self.rotation_z = tk.DoubleVar(value=0)

        self.caxis_adaptive_limits = tk.BooleanVar(value=True)
        self.caxis_limits_high = tk.DoubleVar()
        self.caxis_limits_low = tk.DoubleVar()

        for variable in self.get_variables():
            variable.trace('w',self.on_state_change)

        #self.c.trace('w',self.change_colorbar_type)
        
    def create_widgets(self):
        if globals.debug > 1: print("controls.create_widgets")
        # Update button
        self.update_button = tk.Button(
            self,
            text="Update",
            state='disabled',
            command=self.on_update_button_pressed,
        )
        
        # Axis controls
        self.axes_frame = LabelledFrame(self,"Axes",relief='sunken',bd=1)
        
        self.xaxis_frame = tk.Frame(self.axes_frame)
        self.xaxis_buttons_frame = tk.Frame(self.xaxis_frame)
        
        self.xaxis_label = tk.Label(self.xaxis_frame,text="X Axis")
        self.xaxis_combobox = ttk.Combobox(
            self.xaxis_frame,
            textvariable=self.x,
            state='readonly',
        )
        self.xaxis_linear_button = tk.Radiobutton(
            self.xaxis_buttons_frame,
            text="linear",
            variable=self.xaxis_scale,
            indicatoron=False,
            value="linear",
            padx=5,
            pady=5,
            command=self.set_xaxis_scale,
        )
        self.xaxis_log_button = tk.Radiobutton(
            self.xaxis_buttons_frame,
            text="log10",
            variable=self.xaxis_scale,
            indicatoron=False,
            value="log10",
            padx=5,
            pady=5,
            command=self.set_xaxis_scale,
        )
        self.xaxis_10_button = tk.Radiobutton(
            self.xaxis_buttons_frame,
            text="^10",
            variable=self.xaxis_scale,
            indicatoron=False,
            value="^10",
            padx=5,
            pady=5,
            command=self.set_xaxis_scale,
        )

        self.yaxis_frame = tk.Frame(self.axes_frame)
        self.yaxis_buttons_frame = tk.Frame(self.yaxis_frame)
        
        self.yaxis_label = tk.Label(self.yaxis_frame,text="Y Axis")
        self.yaxis_combobox = ttk.Combobox(
            self.yaxis_frame,
            textvariable=self.y,
            state='readonly',
        )
        self.yaxis_linear_button = tk.Radiobutton(
            self.yaxis_buttons_frame,
            text="linear",
            variable=self.yaxis_scale,
            indicatoron=False,
            value="linear",
            padx=5,
            pady=5,
            command=self.set_yaxis_scale,
        )
        self.yaxis_log_button = tk.Radiobutton(
            self.yaxis_buttons_frame,
            text="log10",
            variable=self.yaxis_scale,
            indicatoron=False,
            value="log10",
            padx=5,
            pady=5,
            command=self.set_yaxis_scale,
        )
        self.yaxis_10_button = tk.Radiobutton(
            self.yaxis_buttons_frame,
            text="^10",
            variable=self.yaxis_scale,
            indicatoron=False,
            value="^10",
            padx=5,
            pady=5,
            command=self.set_yaxis_scale,
        )


        # Colorbar controls
        self.caxis_frame = LabelledFrame(self,"Colorbar",relief='sunken',bd=1)
        
        self.caxis_label = tk.Label(self.caxis_frame,text="Type")
        self.caxis_combobox = ttk.Combobox(
            self.caxis_frame,
            values = ('None','Column density'),
            textvariable=self.c,
            state='readonly',
        )
        
        self.caxis_buttons_frame = tk.Frame(self.caxis_frame)
        self.caxis_linear_button = tk.Radiobutton(
            self.caxis_buttons_frame,
            text="linear",
            variable=self.caxis_scale,
            indicatoron=False,
            value="linear",
            padx=5,
            pady=5,
            command=self.set_caxis_scale,
            state='disabled',
        )
        self.caxis_log_button = tk.Radiobutton(
            self.caxis_buttons_frame,
            text="log10",
            variable=self.caxis_scale,
            indicatoron=False,
            value="log10",
            padx=5,
            pady=5,
            command=self.set_caxis_scale,
            state='disabled',
        )
        self.caxis_10_button = tk.Radiobutton(
            self.caxis_buttons_frame,
            text="^10",
            variable=self.caxis_scale,
            indicatoron=False,
            value="^10",
            padx=5,
            pady=5,
            command=self.set_caxis_scale,
            state='disabled',
        )

        self.caxis_limits_frame = tk.Frame(self.caxis_frame)
        self.caxis_limits_label = tk.Label(
            self.caxis_limits_frame,
            text="Limits",
        )
        self.caxis_limits_entry_low = FloatEntry(
            self.caxis_limits_frame,
            textvariable=self.caxis_limits_low,
            width=7,
            state='disabled',
        )
        self.caxis_limits_entry_high = FloatEntry(
            self.caxis_limits_frame,
            textvariable=self.caxis_limits_high,
            width=7,
            state='disabled',
        )
        self.caxis_limits_adaptive_button = SwitchButton(
            self.caxis_limits_frame,
            text="Adaptive",
            variable=self.caxis_adaptive_limits,
            command=(
                lambda *args,**kwargs: self.disable('colorbar limits'),
                lambda *args,**kwargs: self.enable('colorbar limits'),
            ),
            state='disabled',
        )
        

        # Plot controls
        self.plot_controls_frame = LabelledFrame(self,"Plot Controls",relief='sunken',bd=1)
        self.point_size_label = tk.Label(self.plot_controls_frame,text='Point size (px)')
        self.point_size_entry = IntegerEntry(self.plot_controls_frame,textvariable=self.point_size,disallowed_values=[0])

        self.rotations_frame = tk.Frame(self.plot_controls_frame)
        self.rotation_label = tk.Label(self.rotations_frame,text="Rotation (x,y,z deg)")
        self.rotation_x_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_x,width=5)
        self.rotation_y_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_y,width=5)
        self.rotation_z_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_z,width=5)
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x')
        
        # Axis controls
        self.xaxis_label.grid(row=0,column=0)
        self.xaxis_combobox.grid(row=0,column=1,sticky='ew')
        self.xaxis_linear_button.pack(side='left')
        self.xaxis_log_button.pack(side='left')
        self.xaxis_10_button.pack(side='left')

        self.xaxis_buttons_frame.grid(row=1,column=0,columnspan=2,sticky='ne')
        self.xaxis_frame.grid(row=0,column=0,sticky='new')

        self.yaxis_label.grid(row=0,column=0)
        self.yaxis_combobox.grid(row=0,column=1,sticky='ew')
        self.yaxis_linear_button.pack(side='left')
        self.yaxis_log_button.pack(side='left')
        self.yaxis_10_button.pack(side='left')

        self.yaxis_buttons_frame.grid(row=1,column=0,columnspan=2,sticky='ne')
        self.yaxis_frame.grid(row=1,column=0,sticky='new')
        
        self.xaxis_frame.columnconfigure(1,weight=1)
        self.yaxis_frame.columnconfigure(1,weight=1)

        self.axes_frame.columnconfigure(0,weight=1)
        self.axes_frame.pack(side='top',fill='both')

        # Colorbar controls
        self.caxis_label.grid(row=0,column=0)
        self.caxis_combobox.grid(row=0,column=1,sticky='ew')

        self.caxis_linear_button.pack(side='left')
        self.caxis_log_button.pack(side='left')
        self.caxis_10_button.pack(side='left')

        self.caxis_buttons_frame.grid(row=1,column=0,columnspan=2,sticky='ne')

        self.caxis_limits_label.grid(row=0,column=0)
        self.caxis_limits_entry_low.grid(row=0,column=1)
        self.caxis_limits_entry_high.grid(row=0,column=2)
        self.caxis_limits_adaptive_button.grid(row=0,column=3)

        self.caxis_limits_frame.grid(row=2,column=0,columnspan=2)
        
        self.caxis_frame.columnconfigure(1,weight=1)
        self.caxis_frame.pack(side='top',fill='both')


        # Plot controls
        self.point_size_label.grid(row=0,column=0)
        self.point_size_entry.grid(row=0,column=1)
        
        self.rotation_label.grid(row=0,column=0)
        self.rotation_x_entry.grid(row=0,column=1)
        self.rotation_y_entry.grid(row=0,column=2)
        self.rotation_z_entry.grid(row=0,column=3)

        self.rotations_frame.grid(row=1,column=0,columnspan=2)
        
        self.plot_controls_frame.pack(side='top')

    def on_state_change(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_state_change")
        # Compare the current state to the previous state
        if self.saved_state is None: return
        current_state = self.get_state()
        for item in current_state:
            if item not in self.saved_state:
                self.update_button.configure(state='normal')
                break
        else:
            self.update_button.configure(state='disabled')

    def get_state(self,*args,**kwargs):
        if globals.debug > 1: print("controls.get_state")
        state = []
        for v in self.get_variables():
            try:
                state.append([v,v.get()])
            except: pass
        return state

    def save_state(self,*args,**kwargs):
        if globals.debug > 1: print("controls.save_state")
        self.saved_state = self.get_state()
        self.update_button.configure(state='disabled')

    def get_variables(self,*args,**kwargs):
        if globals.debug > 1: print("controls.get_variables")
        variables = []
        for name in dir(self):
            attr = getattr(self,name)
            if isinstance(attr,(tk.IntVar,tk.DoubleVar,tk.StringVar,tk.BooleanVar)):
                variables.append(attr)
        return variables
        
    def update_axis_comboboxes(self,data):
        if globals.debug > 1: print("controls.update_axis_comboboxes")
        # Update the values in the comboboxes with the keys in data
        if not isinstance(data,OrderedDict):
            raise TypeError("The data read from a file in read_file must be of type 'OrderedDict', not '"+type(data).__name__+"'")

        data_keys = data['data'].keys()
        for data_key in ['x','y','z','m','h']:
            if data_key not in data_keys:
                raise ValueError("Could not find required key '"+data_key+"' in the data from read_file")

        keys = []
        N = len(data['data']['x'])
        for key,val in data['data'].items():
            if hasattr(val,"__len__"):
                if len(val) == N: keys.append(key)
        
        self.xaxis_combobox.config(values=keys)
        self.yaxis_combobox.config(values=keys)
    
    def change_colorbar_type(self,*args,**kwargs):
        if globals.debug > 1: print("controls.change_colorbar_type")
        self.gui.interactiveplot.set_draw_type(self.c.get())
        if self.c.get() == "Column density":
            self.x.set('x')
            self.y.set('y')
        if self.c.get() != 'None': self.enable('colorbar')

    def set_xaxis_scale(self,*args,**kwargs):
        if globals.debug > 1: print("controls.set_xaxis_scale")
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.xscale = self.xaxis_scale.get()
    def set_yaxis_scale(self,*args,**kwargs):
        if globals.debug > 1: print("controls.set_yaxis_scale")
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.yscale = self.yaxis_scale.get()
    def set_caxis_scale(self,*args,**kwargs):
        if globals.debug > 1: print("controls.set_caxis_scale")
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.cscale = self.caxis_scale.get()

    def get_all_children(self, finList=[], wid=None):
        if globals.debug > 1: print("controls.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
            
    def disable(self,group,temporarily=False):
        if globals.debug > 1: print("controls.disable")
        if group == 'all': children = self.get_all_children()
        elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
        elif group == 'colorbar': children = self.get_all_children(wid=self.caxis_frame)
        elif group == 'colorbar limits': children = [self.caxis_limits_entry_low,self.caxis_limits_entry_high]

        if temporarily: self.previous_state = self.get_widget_state(children)
        else: self.previous_state = None
        
        self.set_widget_state(children,'disabled')

    def enable(self,group):
        if globals.debug > 1: print("controls.enable")
        if self.previous_state is not None:
            for widget,state in self.previous_state:
                widget.configure(state=state)
            self.previous_state = None
        else:
            if group == 'all': children = self.get_all_children()
            elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
            elif group == 'colorbar':
                children = self.get_all_children(wid=self.caxis_frame)
                # Don't enable the colorbar limits entries if we are using adaptive limits
                if self.caxis_adaptive_limits.get():
                    if self.caxis_limits_entry_low in children: children.remove(self.caxis_limits_entry_low)
                    if self.caxis_limits_entry_high in children: children.remove(self.caxis_limits_entry_high)
            elif group == 'colorbar limits': children = [self.caxis_limits_entry_low,self.caxis_limits_entry_high]
            self.set_widget_state(children,'normal')

    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("controls.set_widget_state")
        for widget in widgets:
            if 'state' in widget.configure():
                current_state = widget.cget('state')
                if current_state != state:
                    if isinstance(widget,ttk.Combobox):
                        if state == 'normal': widget.configure(state='readonly')
                    else:
                        widget.configure(state=state)

    def get_widget_state(self,widgets):
        if globals.debug > 1: print("controls.get_widget_state")
        states = []
        for widget in widgets:
            if 'state' in widget.configure():
                states.append([widget,widget.cget('state')])
        return states
                        
    def on_update_button_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_update_button_pressed")
        
        self.save_state()
        #self.gui.set_user_controlled(False)
        
        # Perform any rotations necessary
        #self.gui.data.reset()
        self.gui.data.rotate(
            self.rotation_x.get(),
            self.rotation_y.get(),
            self.rotation_z.get(),
        )


        # Draw the new plot
        self.gui.interactiveplot.update()
        #self.gui.set_user_controlled(True)

