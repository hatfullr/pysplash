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

from functions.getwidgetsstates import get_widgets_states
from functions.setwidgetsstates import set_widgets_states
from functions.getallchildren import get_all_children
from functions.hotkeystostring import hotkeys_to_string
from functions.colorbarrealquantityprompt import ColorbarRealQuantityPrompt

from widgets.tooltip import ToolTip
from widgets.button import Button
from widgets.labelledframe import LabelledFrame
from widgets.axiscontroller import AxisController
from widgets.verticalscrolledframe import VerticalScrolledFrame
from widgets.comboboxchoicecontrols import ComboboxChoiceControls

from lib.tkvariable import StringVar
from widgets.radiobutton import RadioButton

import matplotlib
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
        self.previous_colorbar_type = None
        
        self.gui.bind("<<PlotUpdate>>",self.on_plot_update,add="+")

        self.current_state = None
        self.previous_state = None
        self.saved_state = None
        
        self.bid = self.winfo_toplevel().bind("<Visibility>", self.on_visible, add="+")

        self.axis_controllers['XAxis'].combobox.bind("<<ComboboxSelected>>", self.update_colorbar_controller, add="+")
        self.axis_controllers['YAxis'].combobox.bind("<<ComboboxSelected>>", self.update_colorbar_controller, add="+")
        self.axis_controllers['XAxis'].combobox.bind("<<ComboboxSelected>>", self.update_yaxis_controller, add="+")
        self.axis_controllers['YAxis'].combobox.bind("<<ComboboxSelected>>", self.update_xaxis_controller, add="+")
        self.axis_controllers['Colorbar'].combobox.mathentry.allowempty = True

        self.colorbar_cmap_combobox.bind("<Return>", lambda *args, **kwargs: self.focus(), add="+")
        
        
        self.previous_colorbar_type = self.colorbar_type.get()
        def save_previous_colorbar_type(event):
            self.previous_colorbar_type = event.widget.value
        
        self.colorbar_integrated_button.bind("<<ButtonReleased>>", save_previous_colorbar_type, add='+')
        self.colorbar_surface_button.bind("<<ButtonReleased>>", save_previous_colorbar_type, add='+')
        
        self.initialized = False

    # This callback function runs a single time, after the application has been loaded
    def on_visible(self, *args, **kwargs):
        self.current_state = {str(v):v.get() for v in globals.state_variables}
        for i,variable in enumerate(globals.state_variables):
            variable.trace('w', self.on_state_change)
        self.winfo_toplevel().unbind("<Visibility>", self.bid)
        self.save_state()
        
    def create_variables(self):
        if globals.debug > 1: print("controls.create_variables")
        self.colorbar_type = StringVar(self, "integrated", "colorbar_type")
        self.colorbar_real_mode = StringVar(self, None, "colorbar_real_mode")
        self.colorbar_cmap = StringVar(self, matplotlib.rcParams['image.cmap'], "colorbar_cmap")
        globals.state_variables.append(self.colorbar_type)

    def create_widgets(self):
        if globals.debug > 1: print("controls.create_widgets")
        # Update button
        self.update_button = Button(
            self,
            text="Update "+hotkeys_to_string('update plot'),
            style="UpdateButton.TButton",
            command=self.on_update_button_pressed,
        )
        ToolTip.createToolTip(self.update_button, "Redraw the plot using the controls below.")
        
        # Axis controls
        self.controls_frame = VerticalScrolledFrame(self,relief='sunken',bd=1)

        xaxis = AxisController(
            self.controls_frame.interior,
            self.gui,
            'XAxis',
            padx=3,pady=3,
            relief='sunken',
        )
        yaxis =AxisController(
            self.controls_frame.interior,
            self.gui,
            'YAxis',
            padx=3,pady=3,
            relief='sunken',
        )
        colorbar = AxisController(
            self.controls_frame.interior,
            self.gui,
            'Colorbar',
            padx=3,pady=3,
            relief='sunken',
        )

        self.colorbar_type_frame = tk.Frame(colorbar)
        self.colorbar_integrated_button = RadioButton(
            self.colorbar_type_frame,
            text="Integrated",
            variable=self.colorbar_type,
            value="integrated"
        )
        ToolTip.createToolTip(
            self.colorbar_integrated_button,
            "Show the quantity as the value integrated through all particle kernels along the line of sight for each pixel (into the screen).",
        )
        self.colorbar_surface_button = RadioButton(
            self.colorbar_type_frame,
            text="Surface",
            variable=self.colorbar_type,
            value="surface",
        )
        ToolTip.createToolTip(
            self.colorbar_surface_button,
            "Show the quantity as the central value of the particle whose kernel is closest to the line of sight for each pixel (into the screen).",
        )
        self.colorbar_real_button = RadioButton(
            self.colorbar_type_frame,
            text="Real",
            variable=self.colorbar_type,
            value="real",
            command=(lambda *args, **kwargs: ColorbarRealQuantityPrompt(self.gui), None),
        )
        ToolTip.createToolTip(
            self.colorbar_real_button,
            "Similar to Integrated except the integration is limited by optical depth. Available only if you supplied either the density and opacity or the particle optical depth.",
        )


        self.colorbar_cmap_frame = tk.LabelFrame(colorbar, text="Colormap")
        def validate(value):
            success = value in list(self.colorbar_cmap_combobox['values'])
            if not success: self.colorbar_cmap_combobox.flash()
            return success
        self.colorbar_cmap_combobox = ComboboxChoiceControls(
            self.colorbar_cmap_frame,
            values=list(matplotlib.colormaps.keys()),
            textvariable=self.colorbar_cmap,
            validate='focusout',
            validatecommand=(self.register(validate), '%P'),
        )
            
        

        self.axis_controllers = {
            'XAxis' : xaxis,
            'YAxis' : yaxis,
            'Colorbar' : colorbar,
        }
        
        # Plot controls
        self.plotcontrols = PlotControls(self.controls_frame.interior,self.gui,padx=3,pady=3,relief='sunken')
    
    def place_widgets(self):
        if globals.debug > 1: print("controls.place_widgets")
        # Update button
        self.update_button.pack(side='top',fill='x',padx=5,pady=5)
        
        # Axis controls
        self.colorbar_integrated_button.pack(side='left',fill='both',expand=True)
        self.colorbar_surface_button.pack(side='left',fill='both',expand=True)
        self.colorbar_real_button.pack(side='left',fill='both',expand=True)
        self.colorbar_type_frame.pack(side='top',fill='both',expand=True,pady=(5,0))

        self.colorbar_cmap_combobox.pack(fill='both',expand=True)
        self.colorbar_cmap_frame.pack(side='top',fill='x')
        
        for axis_name,axis_controller in self.axis_controllers.items():
            axis_controller.pack(side='top',fill='x')

        # Plot controls
        self.plotcontrols.pack(side='top',fill='x')

        self.controls_frame.pack(side='top',fill='both',expand=True)
        self.controls_frame.interior.configure(padx=5,pady=5)

    def on_state_change(self,*args,**kwargs):
        if globals.debug > 1: print("controls.on_state_change")
        
        # If the state is changing because a variable has been modified
        if len(args) >= 1:
            variable = args[0]
        
            # This needs to happen always
            var = self.string_to_state_variable(variable)
            if var is not None:
                self.current_state[variable] = var.get()

        # We can indicate a change in state even if a variable has not been modified
        
        # Don't mess with the update button any time that we're pressing hotkeys
        if globals.hotkey_pressed: return
        # Compare the current state to the previous state
        if self.saved_state is None: return

        if len(self.compare_states(self.current_state,self.saved_state)) > 0:
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
        if not need_full_redraw:
            for axis_controller in self.axis_controllers.values():
                if axis_controller.value in changed_variables:
                    need_full_redraw = True
                    break

        # If the axis labels changed, then we only need a quick update
        if not need_quick_redraw:
            for axis_controller in self.axis_controllers.values():
                if axis_controller.label in changed_variables:
                    need_quick_redraw = True
                    break

        # If the point size changed, we need a full redraw
        if not need_full_redraw and self.gui.controls.plotcontrols.point_size in changed_variables:
            need_full_redraw=True

        # Check if the user changed any of the x or y axis limits (changing units and scales also changes limits)
        if self.is_limits_changed(('XAxis','YAxis')):
            # Cancel any queued zoom
            self.gui.plottoolbar.cancel_queued_zoom()
            
            user_xlims = self.axis_controllers['XAxis'].limits.get()
            user_ylims = self.axis_controllers['YAxis'].limits.get()
            
            if np.isnan(user_xlims[0]): user_xlims = (None, user_xlims[1])
            if np.isnan(user_xlims[1]): user_xlims = (user_xlims[0], None)
            if np.isnan(user_ylims[0]): user_ylims = (None, user_ylims[1])
            if np.isnan(user_ylims[1]): user_ylims = (user_ylims[0], None)
            
            # Now set the new axis limits
            self.gui.interactiveplot.ax.set_xlim(user_xlims)
            self.gui.interactiveplot.ax.set_ylim(user_ylims)

            need_full_redraw = True
            
            """
            # Check if any of the plot's data is outside these limits
            xlim, ylim = self.gui.interactiveplot.calculate_xylim(which='both')
            if (all([xl is not None for xl in xlim]) and
                all([xl is not None for xl in user_xlims]) and
                all([yl is not None for yl in ylim]) and
                all([yl is not None for yl in user_ylims])):
                if (min(xlim) < min(user_xlims) or max(xlim) > max(user_xlims) or
                    min(ylim) < min(user_ylims) or max(ylim) > max(user_ylims)):
                    need_full_redraw = True
            else:
                need_full_redraw = True

            # Check if the image's extents cut off any data
            if self.gui.interactiveplot.drawn_object is not None:
                extent = np.array(self.gui.interactiveplot.drawn_object._extent)
                exlim = extent[:2]
                eylim = extent[2:]
                if (min(exlim) > min(xlim) or max(exlim) < max(xlim) or
                    min(eylim) > min(ylim) or max(eylim) < max(ylim)):
                    need_full_redraw = True
                    
            # Check if the scale has changed for x and y axes only
            for key in ['XAxis','YAxis']:
                if self.axis_controllers[key].scale.get() != self.previous_axis_scales[key]:
                    need_full_redraw = True
                    break
            """
            

        if self.is_limits_changed(('Colorbar')):
            user_clims = self.axis_controllers['Colorbar'].limits.get()
            if np.isnan(user_clims[0]): user_clims = (None, user_clims[1])
            if np.isnan(user_clims[1]): user_clims = (user_clims[0], None)
            self.gui.interactiveplot.colorbar.set_clim(user_clims)
            need_quick_redraw = True

        # Check if the colorbar's scale has changed
        if (self.gui.interactiveplot.colorbar.visible and
            self.axis_controllers['Colorbar'].scale.get() != self.previous_axis_scales['Colorbar']):
            need_quick_redraw = True
        
        # Perform the queued zoom if there is one
        if self.gui.plottoolbar.queued_zoom:
            self.gui.plottoolbar.queued_zoom()
            need_full_redraw = True
        
        # Perform any rotations necessary
        if (self.plotcontrols.rotation_x in changed_variables or
            self.plotcontrols.rotation_y in changed_variables or
            self.plotcontrols.rotation_z in changed_variables):
            self.gui.data.rotate(
                self.plotcontrols.rotation_x.get(),
                self.plotcontrols.rotation_y.get(),
                self.plotcontrols.rotation_z.get(),
            )
            need_full_redraw = True

        # Redraw when colorbar type changed
        if (not need_full_redraw and
            self.colorbar_type in changed_variables):
            need_full_redraw = True

        # Save the previous scales
        for key,axis_controller in self.axis_controllers.items():
            self.previous_axis_scales[key] = axis_controller.scale.get()

        # Save the previous Integrated/Surface value
        self.previous_colorbar_type = self.colorbar_type.get()
                
        # Draw the new plot
        if need_full_redraw:
            self.gui.interactiveplot.update()
            # Everything after this is done in interactiveplot.after_calculate
            # because we need to wait for the plot to finish calculating
        elif need_quick_redraw:
            self.gui.interactiveplot.draw()
        
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

        # Store the axis limits
        self.previous_xaxis_limits = self.gui.interactiveplot.ax.get_xlim()
        self.previous_yaxis_limits = self.gui.interactiveplot.ax.get_ylim()
        self.previous_caxis_limits = self.gui.interactiveplot.colorbar.get_cax_limits()
        self.save_state()

    def update_colorbar_controller(self,*args,**kwargs):
        if globals.debug > 1: print("controls.update_colorbar_controller")

        if (not self.gui.time_mode.get() and
            (self.axis_controllers['XAxis'].value.get() not in ['x','y','z'] or
            self.axis_controllers['YAxis'].value.get() not in ['x','y','z'])):
            if self.axis_controllers['Colorbar'].value.get() not in ['Point Density','','None',None]:
                self.axis_controllers['Colorbar'].value.set("")
            
            for choice in list(self.axis_controllers['Colorbar'].combobox['values']):
                if choice not in ['',None,'None','Point Density']:
                    self.axis_controllers['Colorbar'].combobox.disable_choice(choice)

    # When the YAxis combobox is selected, disable the option in the XAxis combobox
    def update_xaxis_controller(self,*args,**kwargs):
        if globals.debug > 1: print("controls.update_xaxis_controller")
        xaxis = self.axis_controllers['XAxis']
        yaxis = self.axis_controllers['YAxis']
        value = yaxis.value.get()
        xvalues = list(xaxis.combobox['values'])
        yvalues = list(yaxis.combobox['values'])
        if value in xvalues: xaxis.combobox.disable_choice(value)
        if hasattr(self,"previous_yaxis_value") and self.previous_yaxis_value != value:
            if self.previous_yaxis_value in xvalues: xaxis.combobox.enable_choice(self.previous_yaxis_value)
        self.previous_yaxis_value = value
        
    def update_yaxis_controller(self,*args,**kwargs):
        if globals.debug > 1: print("controls.update_yaxis_controller")
        xaxis = self.axis_controllers['XAxis']
        yaxis = self.axis_controllers['YAxis']
        value = xaxis.value.get()
        xvalues = list(xaxis.combobox['values'])
        yvalues = list(yaxis.combobox['values'])
        if value in yvalues: yaxis.combobox.disable_choice(value)
        if hasattr(self,"previous_xaxis_value") and self.previous_xaxis_value != value:
            if self.previous_xaxis_value in yvalues: yaxis.combobox.enable_choice(self.previous_xaxis_value)
        self.previous_xaxis_value = value

