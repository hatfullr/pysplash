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
from widgets.button import Button
from matplotlib.axis import XAxis, YAxis
import numpy as np
from copy import copy
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

        # Store a list of this widget's children for increased performance
        # over updating the list of children all the time
        self._children = get_all_children(self)

        self.previous_xaxis_limits = None
        self.previous_yaxis_limits = None
        self.previous_caxis_limits = None
        
        self.gui.bind("<<PlotUpdate>>",self.on_plot_update,add="+")

        self.current_state = None
        self.saved_state = None
        #self.previous_state = None

        # This callback function runs a single time, after the application has been loaded
        def callback(*args,**kwargs):
            self.current_state = {str(v):v.get() for v in globals.state_variables}
            self.save_state()
            for variable in globals.state_variables:
                variable.trace('w',self.on_state_change)
            self.winfo_toplevel().unbind("<Visibility>", bid)
        bid = self.winfo_toplevel().bind("<Visibility>", callback, add="+")

        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")

    def create_widgets(self):
        if globals.debug > 1: print("controls.create_widgets")
        # Update button
        self.update_button = Button(
            self,
            text="Update "+hotkeys_to_string('update plot'),
            state='disabled',
            command=self.on_update_button_pressed,
        )
        ToolTip.createToolTip(self.update_button, "Redraw the plot using the controls below.")
        
        # Axis controls
        self.axes_frame = LabelledFrame(self,"Axes",relief='sunken',bd=1)
        self.axis_controllers = {
            'XAxis' : AxisController(self,self.gui,'XAxis',padx=3,pady=3,relief='sunken'),
            'YAxis' : AxisController(self,self.gui,'YAxis',padx=3,pady=3,relief='sunken'),
            'Colorbar' : AxisController(self,self.gui,'Colorbar',padx=3,pady=3,relief='sunken',usecombobox=False),
        }
        
        # Plot controls
        self.plotcontrols = PlotControls(self,self.gui,padx=3,pady=3,relief='sunken')
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x')
        
        # Axis controls
        for axis_name,axis_controller in self.axis_controllers.items():
            axis_controller.pack(side='top',fill='x')

        # Plot controls
        self.plotcontrols.pack(side='top',fill='x')
        
    def on_state_change(self,variable,index,mode):
        if globals.debug > 1: print("controls.on_state_change")
        # Don't mess with the update button any time that we're pressing hotkeys
        if globals.hotkey_pressed: return
        # Compare the current state to the previous state
        if self.saved_state is None: return

        strlist = [str(v) for v in globals.state_variables]
        var = globals.state_variables[strlist.index(variable)]
        value = var.get()

        self.current_state[variable] = value
        
        if len(self.compare_states(self.current_state,self.saved_state)) > 0:
            self.update_button.configure(state='!disabled',relief='raised')
        else:
            self.update_button.configure(state='disabled',relief='sunken')

    def string_to_state_variable(self, string):
        if globals.debug > 1: print("controls.string_to_state_variable")
        strlist = [str(v) for v in globals.state_variables]
        return globals.state_variables[strlist.index(string)]

    def compare_states(self, state1, state2):
        if globals.debug > 1: print("controls.compare_states")
        changed_variables = []
        for key, value in state1.items():
            if state2[key] != value: changed_variables.append(self.string_to_state_variable(key))
        return changed_variables

    def save_state(self,*args,**kwargs):
        if globals.debug > 1: print("controls.save_state")
        self.saved_state = copy(self.current_state)
        self.update_button.configure(state='disabled',relief='sunken')
    
    def disable(self,temporarily=False):
        if globals.debug > 1: print("controls.disable")
        
        if temporarily: self.previous_state = get_widgets_states(self._children)
        else: self.previous_state = None
        
        set_widgets_states(self._children,'disabled')

    def enable(self):
        if globals.debug > 1: print("controls.enable")
        if self.previous_state is not None:
            for widget,state in self.previous_state:
                widget.configure(state=state)
            self.previous_state = None
        else:
            set_widgets_states(self._children,'normal')
    

    def is_limits_changed(self, which):
        if globals.debug > 1: print("controls.is_limits_changed")

        # Check if the user changed some of the axis limits in the controls panel
        ax = self.gui.interactiveplot.ax
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        vmin, vmax = self.gui.interactiveplot.colorbar.get_cax_limits()

        if isinstance(which, str):
            user_lims = self.axis_controllers[which].limits.get()
            if which == 'XAxis':
                lims = (xmin,xmax)
                plims = self.previous_xaxis_limits
            elif which == 'YAxis':
                lims = (ymin,ymax)
                plims = self.previous_yaxis_limits
            elif which == 'Colorbar':
                lims = (vmin,vmax)
                plims = self.previous_caxis_limits
            else: raise ValueError("Received argument",which,"but expected one of 'XAxis', 'YAxis', or 'Colorbar'")
            return lims != plims or lims != user_lims

            
        elif isinstance(which, (list, tuple, np.ndarray)):
            if all([isinstance(w,str) for w in which]):
                return any([self.is_limits_changed(w) for w in which])
            else: raise TypeError("All elements in the input list, tuple, or np.ndarray must be of type 'str'")
        else: raise TypeError("Argument must be one of types 'str', 'list', 'tuple', or 'np.ndarray'")

    def on_update_button_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_update_button_pressed")

        need_reset = False
        
        changed_variables = self.compare_states(self.current_state,self.saved_state)

        # If the data file changed, read the new one
        if self.gui.filecontrols.current_file in changed_variables:
            self.gui.read()
            need_reset = True

        # If the x, y, or colorbar axes' combobox/entry values changed
        for axis_controller in self.axis_controllers.values():
            if axis_controller.value in changed_variables:
                need_reset = True
                break

        # Check if the user changed any of the x or y axis limits (changing units also changes limits)
        if self.is_limits_changed(('XAxis','YAxis','Colorbar')):
            # Cancel any queued zoom
            if self.is_limits_changed(('XAxis','YAxis')):
                self.gui.plottoolbar.cancel_queued_zoom()
            
            user_xlims = self.axis_controllers['XAxis'].limits.get()
            user_ylims = self.axis_controllers['YAxis'].limits.get()
            user_clims = self.axis_controllers['Colorbar'].limits.get()
            
            if np.isnan(user_xlims[0]): user_xlims = (None, user_xlims[1])
            if np.isnan(user_xlims[1]): user_xlims = (user_xlims[0], None)
            if np.isnan(user_ylims[0]): user_ylims = (None, user_ylims[1])
            if np.isnan(user_ylims[1]): user_ylims = (user_ylims[0], None)
            if np.isnan(user_clims[0]): user_clims = (None, user_clims[1])
            if np.isnan(user_clims[1]): user_clims = (user_clims[0], None)
            
            # Now set the new axis limits
            self.gui.interactiveplot.ax.set_xlim(user_xlims)
            self.gui.interactiveplot.ax.set_ylim(user_ylims)
            self.gui.interactiveplot.colorbar.set_clim(user_clims)
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
        
        # Draw the new plot
        if need_reset:
            self.gui.interactiveplot.reset()
            self.gui.interactiveplot.update()
            
        # Everything after this is done in interactiveplot.update
        # because we need to wait for the plot to finish calculating

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

    """
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
    """

    def on_plot_update(self, *args, **kwargs):
        if globals.debug > 1: print("controls.on_plot_update")

        # Store the axis limits
        self.previous_xaxis_limits = self.gui.interactiveplot.ax.get_xlim()
        self.previous_yaxis_limits = self.gui.interactiveplot.ax.get_ylim()
        self.previous_caxis_limits = self.gui.interactiveplot.colorbar.get_cax_limits()

        self.save_state()
