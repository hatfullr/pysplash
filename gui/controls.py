from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from plotcontrols import PlotControls
else:
    import tkinter as tk
    import tkinter.ttk as ttk
    from gui.plotcontrols import PlotControls
from collections import OrderedDict
from widgets.labelledframe import LabelledFrame
from widgets.axiscontroller import AxisController
from lib.integratedvalueplot import IntegratedValuePlot
from functions.getwidgetsstates import get_widgets_states
from functions.setwidgetsstates import set_widgets_states
from functions.getallchildren import get_all_children
from functions.hotkeystostring import hotkeys_to_string
from widgets.tooltip import ToolTip
from matplotlib.axis import XAxis, YAxis
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

        
        for variable in self.get_variables():
            variable.trace('w',self.on_state_change)
        
        self.state_listeners_connected = True
        
        self.connect_state_listeners()
        
        self.saved_state = None
        self.previous_state = None

        self.save_state()

        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")

    def create_widgets(self):
        if globals.debug > 1: print("controls.create_widgets")
        # Update button
        self.update_button = tk.Button(
            self,
            text="Update",
            state='disabled',
            command=self.on_update_button_pressed,
        )
        ToolTip.createToolTip(self.update_button, "Redraw the plot using the controls below. Hotkey: "+hotkeys_to_string('update plot'))
        
        # Axis controls
        self.axes_frame = LabelledFrame(self,"Axes",relief='sunken',bd=1)
        self.axis_controllers = {
            'XAxis' : AxisController(self,self.gui,'XAxis',padx=3,pady=3,relief='sunken'),
            'YAxis' : AxisController(self,self.gui,'YAxis',padx=3,pady=3,relief='sunken'),
            'Colorbar' : AxisController(self,self.gui,'Colorbar',padx=3,pady=3,relief='sunken',usecombobox=False),
        }
            
        # Plot controls
        self.plotcontrols = PlotControls(self,padx=3,pady=3,relief='sunken')
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x')
        
        # Axis controls
        for axis_name,axis_controller in self.axis_controllers.items():
            axis_controller.pack(side='top',fill='x')

        # Plot controls
        self.plotcontrols.pack(side='top',fill='x')

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
            if self.gui.plottoolbar.queued_zoom is not None:
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

        variables.append(self.gui.filecontrols.current_file)
        for child in get_all_children(self):
            if hasattr(child,"get_variables"):
                variables += child.get_variables()
        
        for name in dir(self):
            attr = getattr(self,name)
            if isinstance(attr,(tk.IntVar,tk.DoubleVar,tk.StringVar,tk.BooleanVar)):
                variables.append(attr)
        return variables
    
    def disable(self,temporarily=False):
        if globals.debug > 1: print("controls.disable")
        
        children = get_all_children(self)
        if temporarily: self.previous_state = get_widgets_states(children)
        else: self.previous_state = None
        
        set_widgets_states(children,'disabled')

    def enable(self):
        if globals.debug > 1: print("controls.enable")
        if self.previous_state is not None:
            for widget,state in self.previous_state:
                widget.configure(state=state)
            self.previous_state = None
        else:
            children = get_all_children(self)
            set_widgets_states(children,'normal')
    

    def is_limits_changed(self, which):
        if globals.debug > 1: print("controls.is_limits_changed")

        # Check if the user changed some of the axis limits in the controls panel
        ax = self.gui.interactiveplot.ax
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        vmin, vmax = self.gui.interactiveplot.colorbar.get_cax_limits()

        if isinstance(which, str):
            user_min, user_max = self.get_user_axis_limits(which)
            if which == 'XAxis': return xmin != user_min or xmax != user_max
            elif which == 'YAxis': return ymin != user_min or ymax != user_max
            elif which == 'Colorbar': return vmin != user_min or vmax != user_max
            else: raise ValueError("Received argument",which,"but expected one of 'XAxis', 'YAxis', or 'Colorbar'")
        elif isinstance(which, (list, tuple, np.ndarray)):
            if all([isinstance(w,str) for w in which]):
                return any([self.is_limits_changed(w) for w in which])
            else: raise TypeError("All elements in the input list, tuple, or np.ndarray must be of type 'str'")
        else: raise TypeError("Argument must be one of types 'str', 'list', 'tuple', or 'np.ndarray'")

    def get_user_axis_limits(self, which):
        if globals.debug > 1: print("controls.get_axis_limits")
        return self.axis_controllers[which].limits.low.get(), self.axis_controllers[which].limits.high.get()
    
    def on_update_button_pressed(self,*args,**kwargs):
        if not self.state_listeners_connected: return
        if globals.debug > 1: print("controls.on_update_button_pressed")

        # We do the following update step to make sure focus has been released from the
        # entry widgets. Otherwise, we do not register any change in the entry widgets.
        # Send the focus to the root widget
        self.winfo_toplevel().focus()
        # Update the focus
        self.update()

        need_reset = False
        redraw_canvas = False
        
        changed_variables = self.get_which_variables_changed_between_states(self.get_state(),self.saved_state)

        # If the data file changed, read the new one
        if self.gui.filecontrols.current_file in changed_variables:
            self.gui.read()
            need_reset = True

        # If the x, y, or colorbar axes' combobox values or units changed
        for axis_controller in self.axis_controllers.values():
            if (axis_controller.value in changed_variables or # Values
                axis_controller.units.value in changed_variables): # Units
                need_reset = True
                break
                #if any(self.gui.get_display_data(axis_controller.value.get(), scaled=False) <= 0):
                #    axis_controller.scale.linear_button.invoke()
                

        # Check if the user changed any of the x or y axis limits
        if self.is_limits_changed(('XAxis','YAxis')):
            # Cancel any queued zoom
            self.gui.plottoolbar.cancel_queued_zoom()
            
            user_xmin, user_xmax = self.get_user_axis_limits('XAxis')
            user_ymin, user_ymax = self.get_user_axis_limits('YAxis')
            
            if np.isnan(user_xmin): user_xmin = None
            if np.isnan(user_xmax): user_xmax = None
            if np.isnan(user_ymin): user_ymin = None
            if np.isnan(user_ymax): user_ymax = None
            
            # Now set the new axis limits
            self.gui.interactiveplot.ax.set_xlim(user_xmin, user_xmax)
            self.gui.interactiveplot.ax.set_ylim(user_ymin, user_ymax)
            need_reset = True
            
        
        # Perform the queued zoom if there is one
        if self.gui.plottoolbar.queued_zoom:
            self.gui.plottoolbar.queued_zoom()
            need_reset = True
        
        # Perform any rotations necessary
        if (self.plotcontrols.rotation_x in changed_variables or
            self.plotcontrols.rotation_y in changed_variables or
            self.plotcontrols.rotation_z in changed_variables):
            if self.gui.data is not None:
                self.gui.data.rotate(
                    self.plotcontrols.rotation_x.get(),
                    self.plotcontrols.rotation_y.get(),
                    self.plotcontrols.rotation_z.get(),
                )
                need_reset = True

        # Check if the user changed the colorbar axis limits
        if self.is_limits_changed('Colorbar'):
            # If we aren't going to be resetting the plot, then simply update
            # the colorbar limits. This will automatically update the colors in the image
            if not need_reset:
                self.gui.interactiveplot.colorbar.set_clim(self.get_user_axis_limits('Colorbar'))
                self.gui.interactiveplot.canvas.draw_idle()
        
        # Draw the new plot
        if need_reset:
            self.gui.interactiveplot.reset()
            self.gui.interactiveplot.update()
        elif redraw_canvas:
            self.gui.interactiveplot.canvas.draw_idle()
        
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
