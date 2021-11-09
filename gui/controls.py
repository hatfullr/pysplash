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

class Controls(tk.Frame,object):
    def __init__(self,gui,*args,**kwargs):
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
        
    def create_variables(self):
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

        self.c.trace('w',self.change_colorbar_type)
        
    def create_widgets(self):
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
            width=7
        )
        self.caxis_limits_entry_high = FloatEntry(
            self.caxis_limits_frame,
            textvariable=self.caxis_limits_high,
            width=7
        )
        self.caxis_limits_adaptive_button = SwitchButton(
            self.caxis_limits_frame,
            text="Adaptive",
            variable=self.caxis_adaptive_limits,
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
        
        self.plot_controls_frame.pack(side='top')#,fill='both')

    def update_axis_comboboxes(self,data):
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
        self.gui.interactiveplot.set_draw_type(self.c.get())
        if self.c.get() == "Column density":
            self.x.set('x')
            self.y.set('y')

    def set_xaxis_scale(self,*args,**kwargs):
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.set_scale(self.xaxis_scale.get())
    def set_yaxis_scale(self,*args,**kwargs):
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.set_scale(self.yaxis_scale.get())
    def set_caxis_scale(self,*args,**kwargs):
        drawn_object = self.gui.interactiveplot.drawn_object
        if drawn_object is not None:
            drawn_object.set_scale(self.caxis_scale.get())

    def get_all_children(self, finList=[], wid=None):
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
            
    def disable(self,group):
        if group == 'all': children = self.get_all_children()
        elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
        elif group == 'colorbar': children = self.get_all_children(wid=self.caxis_frame)
        self.set_state(children,'disabled')

    def enable(self,group):
        if group == 'all': children = self.get_all_children()
        elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
        elif group == 'colorbar': children = self.get_all_children(wid=self.caxis_frame)
        self.set_state(children,'normal')

    def set_state(self,widgets,state):
        for widget in widgets:
            if 'state' in widget.configure():
                if isinstance(widget,ttk.Combobox):
                    if state == 'normal': widget.configure(state='readonly')
                else:
                    widget.configure(state=state)
