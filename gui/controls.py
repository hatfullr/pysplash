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
from widgets.axiscontroller import AxisController
from lib.integratedvalueplot import IntegratedValuePlot
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

        self.axis_names = [
            'XAxis',
            'YAxis',
            'Colorbar',
        ]
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()


        for variable in self.get_variables():
            variable.trace('w',self.on_state_change)
        
        #self.caxis_combobox.bind("<<ComboboxSelected>>",self.on_caxis_combobox_selected)
        self.saved_state = None
        self.previous_state = None

        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")

        self.point_size = tk.IntVar(value=1)

        self.rotation_x = tk.DoubleVar(value=0)
        self.rotation_y = tk.DoubleVar(value=0)
        self.rotation_z = tk.DoubleVar(value=0)

        self.show_orientation = tk.BooleanVar(value=False)

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

        self.axis_controllers = {}
        for axis_name in self.axis_names:
            self.axis_controllers[axis_name] = AxisController(self,axis_name)

        # Plot controls
        self.plot_controls_frame = LabelledFrame(self,"Plot Controls",relief='sunken',bd=1)
        self.point_size_label = tk.Label(self.plot_controls_frame,text='Point size (px)')
        self.point_size_entry = IntegerEntry(self.plot_controls_frame,textvariable=self.point_size,disallowed_values=[0])

        self.rotations_frame = tk.Frame(self.plot_controls_frame)
        self.rotation_label = tk.Label(self.rotations_frame,text="Rotation (x,y,z deg)")
        self.rotation_x_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_x,width=5)
        self.rotation_y_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_y,width=5)
        self.rotation_z_entry = FloatEntry(self.rotations_frame,textvariable=self.rotation_z,width=5)

        self.orientation_checkbutton = tk.Checkbutton(
            self.plot_controls_frame,
            text="Show orientation",
            variable=self.show_orientation,
        )
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x')
        
        # Axis controls
        for axis_name,axis_controller in self.axis_controllers.items():
            axis_controller.pack(side='top',fill='x')

        # Plot controls
        self.point_size_label.grid(row=0,column=0)
        self.point_size_entry.grid(row=0,column=1)
        
        self.rotation_label.grid(row=0,column=0)
        self.rotation_x_entry.grid(row=0,column=1)
        self.rotation_y_entry.grid(row=0,column=2)
        self.rotation_z_entry.grid(row=0,column=3)

        self.rotations_frame.grid(row=1,column=0,columnspan=2)

        self.orientation_checkbutton.grid(row=2,column=0,columnspan=2,sticky='nws')
        
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
        else: # No break
            if self.gui.plotcontrols.toolbar.queued_zoom is not None:
                self.update_button.configure(state='normal')
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

        for child in self.get_all_children():
            if hasattr(child,"get_variables"): variables += child.get_variables()
            
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

    def on_caxis_combobox_selected(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_caxis_combobox_selected")
        self.change_colorbar_type()
        if self.c.get() == 'None':
            self.disable('colorbar')
            self.enable(self.point_size_entry)
        else:
            self.enable('colorbar')
            self.disable(self.point_size_entry)
        
    def change_colorbar_type(self,*args,**kwargs):
        if globals.debug > 1: print("controls.change_colorbar_type")
        self.gui.interactiveplot.set_draw_type(self.c.get())
        if self.c.get() == "Column density":
            self.x.set('x')
            self.y.set('y')
        if self.c.get() != 'None': self.enable('colorbar')
    
    def get_all_children(self, finList=[], wid=None):
        #if globals.debug > 1: print("controls.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList
            
    def disable(self,group,temporarily=False):
        if globals.debug > 1: print("controls.disable")

        if isinstance(group,str):
            if group == 'all': children = self.get_all_children()
            elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
            elif group == 'xaxis limits': children = [self.xaxis_limits_entry_low,self.xaxis_limits_entry_high]
            elif group == 'yaxis limits': children = [self.yaxis_limits_entry_low,self.yaxis_limits_entry_high]
            elif group == 'colorbar': children = self.get_all_children(wid=self.caxis_frame)
            elif group == 'colorbar limits': children = [self.caxis_limits_entry_low,self.caxis_limits_entry_high]
        else: # Assume this is a widget
            children = group

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
            if isinstance(group,str):
                if group == 'all': children = self.get_all_children()
                elif group == 'axes': children = self.get_all_children(wid=self.xaxis_frame)
                elif group == 'xaxis limits': children = [self.xaxis_limits_entry_low,self.xaxis_limits_entry_high]
                elif group == 'yaxis limits': children = [self.yaxis_limits_entry_low,self.yaxis_limits_entry_high]
                elif group == 'colorbar':
                    children = self.get_all_children(wid=self.caxis_frame)
                    # Don't enable the colorbar limits entries if we are using adaptive limits
                    if self.caxis_limits_entry_low in children: children.remove(self.caxis_limits_entry_low)
                    if self.caxis_limits_entry_high in children: children.remove(self.caxis_limits_entry_high)
                elif group == 'colorbar limits': children = [self.caxis_limits_entry_low,self.caxis_limits_entry_high]
            else: # Assume this is a widget
                children = group
            
            self.set_widget_state(children,'normal')

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

    def get_widget_state(self,widgets):
        if globals.debug > 1: print("controls.get_widget_state")
        if not isinstance(widgets,(list,tuple,np.ndarray)): widgets = [widgets]
        states = []
        for widget in widgets:
            if 'state' in widget.configure():
                if isinstance(widget,tk.Label): continue
                states.append([widget,widget.cget('state')])
        return states
                        
    def on_update_button_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_update_button_pressed")
        
        if (self.gui.interactiveplot.drawn_object is not None and 
            self.saved_state is not None and 
            self.gui.interactiveplot.colorbar_visible):
            for v,val in self.saved_state:
                if v is self.caxis_scale:
                    if val != self.caxis_scale.get():
                        self.gui.interactiveplot.drawn_object.update_cscale(self.caxis_scale.get())
                        self.gui.interactiveplot.update_colorbar_label()

        self.gui.set_user_controlled(False)
        
        if self.gui.plotcontrols.toolbar.queued_zoom is not None:
            self.gui.plotcontrols.toolbar.queued_zoom()
            
        # Perform any rotations necessary
        if self.gui.data is not None:
            self.gui.data.rotate(
                self.rotation_x.get(),
                self.rotation_y.get(),
                self.rotation_z.get(),
            )
        
        # Draw the new plot
        self.gui.interactiveplot.update()
        self.gui.set_user_controlled(True)

        self.save_state()


    def toggle_adaptive_xlim(self,*args,**kwargs):
        if globals.debug > 1: print("controls.toggle_adaptive_xlim")
        self.gui.interactiveplot.toggle_xlim_adaptive()
        if self.xaxis_adaptive_limits.get():
            self.disable('xaxis limits')
        else:
            self.enable('xaxis limits')

    def toggle_adaptive_ylim(self,*args,**kwargs):
        if globals.debug > 1: print("controls.toggle_adaptive_ylim")
        self.gui.interactiveplot.toggle_ylim_adaptive()
        if self.yaxis_adaptive_limits.get():
            self.disable('yaxis limits')
        else:
            self.enable('yaxis limits')
        
        
    def toggle_adaptive_clim(self,*args,**kwargs):
        if globals.debug > 1: print("controls.toggle_adaptive_clim")
        if self.gui.interactiveplot.colorbar_visible:
            self.gui.interactiveplot.toggle_clim_adaptive()
        if self.caxis_adaptive_limits.get():
            self.disable('colorbar limits')
        else:
            self.enable('colorbar limits')
                
    def connect(self):
        # Connect the controls to the interactiveplot
        ax = self.gui.interactiveplot.ax
        self.axis_controllers['XAxis'].connect(ax.xaxis)
        self.axis_controllers['YAxis'].connect(ax.yaxis)
        self.axis_controllers['Colorbar'].connect(self.gui.interactiveplot.cax)
