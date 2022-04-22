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
from gui.customtoolbar import CustomToolbar
import numpy as np
import globals
import inspect # Remove me

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

        # Order is important
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
        
        self.state_listeners_connected = True
        
        self.connect_state_listeners()
        
        self.axis_controllers[self.axis_names[2]].combobox.bind("<<ComboboxSelected>>",self.on_colorbar_combobox_selected)
        
        self.saved_state = None
        self.previous_state = None

        self.save_state()

        
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

    def connect_state_listeners(self,*args,**kwargs):
        if globals.debug > 1: print("controls.connect_state_listeners")
        self.state_listeners_connected = True
        
    def disconnect_state_listeners(self,*args,**kwargs):
        if globals.debug > 1: print('controls.disconnect_state_listeners')
        self.state_listeners_connected = False

    def on_state_change(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_state_change")
        # Compare the current state to the previous state
        if self.saved_state is None: return
        
        current_state = self.get_state()
        for item in current_state:
            if item not in self.saved_state:
                if globals.debug > 1: print("   ",item)
                self.update_button.configure(relief='raised',state='normal')
                break
        else: # No break
            if self.gui.plotcontrols.toolbar.queued_zoom is not None:
                self.update_button.configure(relief='raised',state='normal')
            else:
                self.update_button.configure(relief='sunken',state='disabled')

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
        self.update_button.configure(relief='sunken',state='disabled')

    
    def get_variables(self,*args,**kwargs):
        if globals.debug > 1: print("controls.get_variables")
        variables = []

        variables.append(self.gui.plotcontrols.current_file)

        for child in self.get_all_children():
            if hasattr(child,"get_variables"):
                variables += child.get_variables()
        
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

    def on_colorbar_combobox_selected(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_colorbar_combobox_selected")
        c = self.axis_controllers[self.axis_names[2]].value.get()
        self.gui.interactiveplot.set_draw_type(c)
    
    def get_all_children(self, finList=[], wid=None):
        #if globals.debug > 1: print("controls.get_all_children")
        if wid is None: _list = self.winfo_children()
        else: _list = wid.winfo_children()        
        for item in _list:
            finList.append(item)
            self.get_all_children(finList=finList,wid=item)
        return finList

    
    def disable(self,temporarily=False):
        if globals.debug > 1: print("controls.disable")
        
        children = self.get_all_children()
        if temporarily: self.previous_state = self.get_widget_state(children)
        else: self.previous_state = None
        
        self.set_widget_state(children,'disabled')

    def enable(self):
        if globals.debug > 1: print("controls.enable")
        if self.previous_state is not None:
            for widget,state in self.previous_state:
                widget.configure(state=state)
            self.previous_state = None
        else:
            children = self.get_all_children()
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
        if not self.state_listeners_connected: return
        if globals.debug > 1: print("controls.on_update_button_pressed")

        # We do the following update step to make sure focus has been released from the
        # entry widgets. Otherwise, we do not register any change in the entry widgets.
        # Send the focus to the root widget
        self.winfo_toplevel().focus_set()
        # Update the focus
        self.update()
        
        changed_variables = self.get_which_variables_changed_between_states(self.get_state(),self.saved_state)

        # If the data file changed, read the new one
        if self.gui.plotcontrols.current_file in changed_variables:
            self.gui.read()
        
        """
        if self.gui.interactiveplot.drawn_object is not None and self.saved_state is not None:
            axis_controller_exclusively_changed = None
            for axis_name, axis_controller in self.axis_controllers.items():
                axis_variables = axis_controller.get_variables()
                for variable in changed_variables:
                    if variable is not axis_controller.value and variable not in axis_variables:
                        break
                else:
                    axis_controller_exclusively_changed = axis_controller
                    break

            if axis_controller_exclusively_changed is self.axis_controllers['Colorbar']:
                self.gui.interactiveplot.update_colorbar_label()
        """

        # Check if the user changed any of the x or y axis limits
        ax = self.gui.interactiveplot.ax
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        user_xmin = self.axis_controllers['XAxis'].limits_low.get()
        user_xmax = self.axis_controllers['XAxis'].limits_high.get()
        user_ymin = self.axis_controllers['YAxis'].limits_low.get()
        user_ymax = self.axis_controllers['YAxis'].limits_high.get()
        #print(xmin, user_xmin)
        if xmin != user_xmin or xmax != user_xmax or ymin != user_ymin or ymax != user_ymax:
            # If there is a queued zoom, cancel it, then fire it to remove the rubberband and do normal behavior
            if self.gui.plotcontrols.toolbar.queued_zoom:
                self.gui.plotcontrols.toolbar._zoom_info = None
                self.gui.plotcontrols.toolbar.queued_zoom()

            flag = self.gui.interactiveplot.drawn_object is not None
            if flag: self.gui.interactiveplot.drawn_object._disconnect()
            
            # Now set the new axis limits
            ax.set_xlim(user_xmin, user_xmax)
            ax.set_ylim(user_ymin, user_ymax)

            if flag: self.gui.interactiveplot.drawn_object._connect()
            
            
        
        # Perform the queued zoom if there is one
        if self.gui.plotcontrols.toolbar.queued_zoom is not None:
            # Turn off adaptive limits on both the x and y axes if needed
            for name in self.axis_names[:2]:
                if self.axis_controllers[name].is_adaptive.get():
                    self.axis_controllers[name].limits_adaptive_button.command()
            self.gui.plotcontrols.toolbar.queued_zoom()
                
        # Perform any rotations necessary
        if self.gui.data is not None:
            self.gui.data.rotate(
                self.rotation_x.get(),
                self.rotation_y.get(),
                self.rotation_z.get(),
            )

        # Update the axis 
        #for axis_name, axis_controller in self.axis_controllers.items():
        #    if axis_controller.axis is not None:
        #        axis_controller.axis.set_label(axis_controller.label.get())
        #        self.gui.interactiveplot.canvas.draw()
        #    else:
        #        print("BAD")
            
        # Draw the new plot
        self.gui.interactiveplot.update()
        
        self.save_state()

    def connect(self):
        if globals.debug > 1: print("controls.connect")
        # Connect the controls to the interactiveplot
        ax = self.gui.interactiveplot.ax
        self.axis_controllers['XAxis'].connect(ax.xaxis)
        self.axis_controllers['YAxis'].connect(ax.yaxis)
        if self.gui.interactiveplot.colorbar.side in ['right','left']:
            self.axis_controllers['Colorbar'].connect(self.gui.interactiveplot.colorbar.cax.yaxis)
        else:
            self.axis_controllers['Colorbar'].connect(self.gui.interactiveplot.colorbar.cax.xaxis)

    def get_which_variables_changed_between_states(self,state1,state2):
        if globals.debug > 1: print("controls.get_which_variables_changed_between_states")
        # A state is just a list of tkinter variables and their values
        # [[v0, v0.get()], [v1, v1.get()], ... ]

        result = []
        for item in state1:
            if item not in state2 and item[0] not in result:
                result.append(item[0])
        for item in state2:
            if item not in state1 and item[0] not in result:
                result.append(item[0])
        
        return result
