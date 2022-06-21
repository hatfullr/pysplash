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

from lib.integratedvalueplot import IntegratedValuePlot
from functions.getwidgetsstates import get_widgets_states
from functions.setwidgetsstates import set_widgets_states
from functions.getallchildren import get_all_children
from functions.hotkeystostring import hotkeys_to_string

from widgets.tooltip import ToolTip
from widgets.button import Button
from widgets.labelledframe import LabelledFrame
from widgets.axiscontroller import AxisController
from widgets.verticalscrolledframe import VerticalScrolledFrame

from matplotlib.axis import XAxis, YAxis
import numpy as np
from copy import copy,deepcopy
import globals
import traceback

class Controls(tk.Frame,object):
    update_button_style_initialized = False
    def __init__(self,gui,*args,**kwargs):
        if globals.debug > 1: print("controls.__init__")
        style = ttk.Style()
        
        if not Controls.update_button_style_initialized:
            # Only edit the relief settings of the button style
            
            style.map(
                "UpdateButton.TButton",
                relief = [
                    (['!disabled','!pressed'], style.lookup('TButton','relief',state=['!pressed'])),
                    (['!disabled','pressed'], style.lookup('TButton','relief',state=['pressed'])),
                    ('disabled', style.lookup('TButton','relief',state=['pressed'])),
                ],
            )
            Controls.update_button_style_initialized = True
        
        self.gui = gui
        super(Controls,self).__init__(self.gui,*args,**kwargs)
        
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
        self.previous_axis_scales = {key:None for key in self.axis_controllers.keys()}
        
        self.gui.bind("<<PlotUpdate>>",self.on_plot_update,add="+")

        self.current_state = None
        self.saved_state = None
        
        self.bid = self.winfo_toplevel().bind("<Visibility>", self.on_visible, add="+")
        
        self.initialized = False

    def initialize(self, *args, **kwargs):
        if globals.debug > 1: print("controls.initialize")

        if self.initialized: raise RuntimeError("Controls have already been initialized!")
        
        data = self.gui.data['data']
        
        # Initialize the axis controllers using user's preferences, if there are any
        uninitialized_controllers = []
        for name, axis_controller in self.axis_controllers.items():
            pref = self.gui.get_preference(name)
            if pref is not None:
                if pref['value'] in axis_controller.combobox['values']:
                    axis_controller.value.set(pref['value'])
                    axis_controller.get_data()
                    value_to_set = pref['value']
                    label_to_set = pref['label']
                else:
                    values = list(axis_controller.combobox['values'])
                    value_to_set = ""
                    label_to_set = ""
                    
                    # Choose the first available option that has not been chosen by the other axis controllers
                    available_values = copy(values)
                    for ac in self.axis_controllers.values():
                        value = ac.value.get()
                        if ac is not axis_controller and value in available_values:
                            available_values.remove(value)
                    if len(available_values) > 0:
                        value_to_set = available_values[0]
                        label_to_set = value_to_set
                        
                axis_controller.value.set(value_to_set)
                axis_controller.label.set(label_to_set)
                axis_controller.units.value.set(pref['units'])
                axis_controller.scale.set(pref['scale'])
                if pref['limits'] == 'adaptive': axis_controller.limits.adaptive_on()
                else: axis_controller.limits.set_limits(pref['limits'])
            elif name != 'Colorbar':
                uninitialized_controllers.append(axis_controller)

        """
        # For controllers which did not have their preferences set (except for
        # the Colorbar controller), use the first, second, etc. columns in the data
        if len(uninitialized_controllers) > 0:
            if data is not None:
                cidx = 0
                for i, val in enumerate(data.keys()):
                    if val not in [c.value.get() for c in self.axis_controllers.values()]:
                        uninitialized_controllers[cidx].value.set(val)
                        uninitialized_controllers[cidx].label.set(val)
                        cidx += 1
                        if cidx >= len(uninitialized_controllers): break
        """
        self.initialized = True

    # This callback function runs a single time, after the application has been loaded
    def on_visible(self, *args, **kwargs):
        self.current_state = {str(v):v.get() for v in globals.state_variables}
        for i,variable in enumerate(globals.state_variables):
            variable.trace('w',self.on_state_change)
        self.winfo_toplevel().unbind("<Visibility>", self.bid)
        self.save_state()
        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")

    def create_widgets(self):
        if globals.debug > 1: print("controls.create_widgets")
        # Update button
        self.update_button = Button(
            self,
            text="Update "+hotkeys_to_string('update plot'),
            state='disabled',
            style="UpdateButton.TButton",
            command=self.on_update_button_pressed,
        )
        ToolTip.createToolTip(self.update_button, "Redraw the plot using the controls below.")
        
        # Axis controls
        self.controls_frame = VerticalScrolledFrame(self,relief='sunken',bd=1)
        self.axis_controllers = {
            'XAxis' : AxisController(self.controls_frame.interior,self.gui,'XAxis',padx=3,pady=3,relief='sunken'),
            'YAxis' : AxisController(self.controls_frame.interior,self.gui,'YAxis',padx=3,pady=3,relief='sunken'),
            'Colorbar' : AxisController(self.controls_frame.interior,self.gui,'Colorbar',padx=3,pady=3,relief='sunken'),
        }
        
        # Plot controls
        self.plotcontrols = PlotControls(self.controls_frame.interior,self.gui,padx=3,pady=3,relief='sunken')
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x',padx=5,pady=5)
        
        # Axis controls
        for axis_name,axis_controller in self.axis_controllers.items():
            axis_controller.pack(side='top',fill='x')

        # Plot controls
        self.plotcontrols.pack(side='top',fill='x')

        self.controls_frame.pack(side='top',fill='both',expand=True)
        self.controls_frame.interior.configure(padx=5,pady=5)
        
    def on_state_change(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_state_change")

        # By default, indicate a change in state
        indicate_state_change = True
        
        # If the state is changing because a variable has been modified
        if len(args) >= 1:
            variable = args[0]
        
            # This needs to happen always
            var = self.string_to_state_variable(variable)
            if var is not None:
                self.current_state[variable] = var.get()
            # Do not indicate a state change if the current state is the same as the saved state
            if len(self.compare_states(self.current_state,self.saved_state)) <= 0:
                indicate_state_change = False

        # We can indicate a change in state even if a variable has not been modified
        
        # Don't mess with the update button any time that we're pressing hotkeys
        if globals.hotkey_pressed: return
        # Compare the current state to the previous state
        if self.saved_state is None: return

        if indicate_state_change:
            self.update_button.configure(state='!disabled')
        else:
            self.update_button.configure(state='disabled')

    def string_to_state_variable(self, string):
        if globals.debug > 1: print("controls.string_to_state_variable")
        strlist = [str(v) for v in globals.state_variables]
        if string not in strlist: return None
        return globals.state_variables[strlist.index(string)]

    def compare_states(self, state1, state2):
        if globals.debug > 1: print("controls.compare_states")
        changed_variables = []
        for key, value in state1.items():
            if state2[key] != value: changed_variables.append(self.string_to_state_variable(key))
        return changed_variables

    def save_state(self,*args,**kwargs):
        if globals.debug > 1: print("controls.save_state")
        self.saved_state = deepcopy(self.current_state)
        self.update_button.configure(state='disabled')#,relief='sunken')
    
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
        need_full_redraw = False
        need_quick_redraw = False

        changed_variables = self.compare_states(self.current_state,self.saved_state)
        
        # If the data file changed, read the new one
        if self.gui.filecontrols.current_file in changed_variables:
            self.gui.read()
            need_full_redraw = True
        
        # If the x, y, or colorbar axes' combobox/entry values changed
        for axis_controller in self.axis_controllers.values():
            if axis_controller.value in changed_variables:
                need_full_redraw = True
                break

        # If the axis labels changed, then we only need a quick update
        for axis_controller in self.axis_controllers.values():
            if axis_controller.label in changed_variables:
                need_quick_redraw = True
                break

        # If the point size changed, we need a full redraw
        if self.gui.controls.plotcontrols.point_size in changed_variables:
            need_full_redraw=True

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

            # Check if any of the plot's data is outside these limits
            xlim, ylim = self.gui.interactiveplot.calculate_xylim(which='both')
            if (min(xlim) < min(user_xlims) or max(xlim) > max(user_xlims) or
                min(ylim) < min(user_ylims) or max(ylim) > max(user_ylims)):
                need_full_redraw = True

            # Check if the image's extents cut off any data
            if self.gui.interactiveplot.drawn_object is not None:
                extent = np.array(self.gui.interactiveplot.drawn_object._extent)
                exlim = extent[:2]
                eylim = extent[2:]
                if (min(exlim) > min(xlim) or max(exlim) < max(xlim) or
                    min(eylim) > min(ylim) or max(eylim) < max(ylim)):
                    need_full_redraw = True

            # Check if the scale has changed
            for key,axis_controller in self.axis_controllers.items():
                if axis_controller.scale.get() != self.previous_axis_scales[key]:
                    need_full_redraw = True
                    break
            
        
        # Perform the queued zoom if there is one
        if self.gui.plottoolbar.queued_zoom:
            self.gui.plottoolbar.queued_zoom()
            need_full_redraw = True
        
        # Perform any rotations necessary
        if (self.plotcontrols.rotation_x in changed_variables or
            self.plotcontrols.rotation_y in changed_variables or
            self.plotcontrols.rotation_z in changed_variables):
            self.gui.rotate()
            need_full_redraw = True

        # Save the previous scales
        for key,axis_controller in self.axis_controllers.items():
            self.previous_axis_scales[key] = axis_controller.scale.get()
                
        # Draw the new plot
        if need_full_redraw:
            self.gui.interactiveplot.update()
            self.gui.interactiveplot.canvas.draw()
            # Everything after this is done in interactiveplot.after_calculate
            # because we need to wait for the plot to finish calculating
        elif need_quick_redraw:
            self.gui.interactiveplot.canvas.draw_idle()
        self.save_state()

        # Set the focus to the canvas
        self.gui.interactiveplot.canvas.get_tk_widget().focus_set()

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

    def on_plot_update(self, *args, **kwargs):
        if globals.debug > 1: print("controls.on_plot_update")

        # Update the user's axis preferences
        for name, axis_controller in self.axis_controllers.items():
            pref = {
                'value':axis_controller.value.get(),
                'label':axis_controller.label.get(),
                'units':axis_controller.units.value.get(),
                'limits':axis_controller.limits.get() if not axis_controller.limits.adaptive.get() else 'adaptive',
                'scale':axis_controller.scale.get(),
            }
            self.gui.set_preference(name,pref)
        
        # Store the axis limits
        self.previous_xaxis_limits = self.gui.interactiveplot.ax.get_xlim()
        self.previous_yaxis_limits = self.gui.interactiveplot.ax.get_ylim()
        self.previous_caxis_limits = self.gui.interactiveplot.colorbar.get_cax_limits()
        self.save_state()
