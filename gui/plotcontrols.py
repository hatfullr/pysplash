import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    import tkinter.font as tkFont
from widgets.labelledframe import LabelledFrame
from widgets.integerentry import IntegerEntry
from widgets.floatentry import FloatEntry
from widgets.tooltip import ToolTip
from lib.hotkeys import Hotkeys
from functions.getwidgetsstates import get_widgets_states
from functions.setwidgetsstates import set_widgets_states
from functions.getallchildren import get_all_children
from functions.hotkeystostring import hotkeys_to_string
import globals

class PlotControls(LabelledFrame, object):
    def __init__(self, master, gui, relief='sunken', bd=1, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.__init__")
        super(PlotControls, self).__init__(master, "Plot Controls", *args, relief=relief, bd=bd, **kwargs)
        self.gui = gui
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        self.create_hotkeys()

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.create_variables")
        self.point_size = tk.DoubleVar(value = 1)
        self.rotation_x = tk.DoubleVar(value = 0.)
        self.rotation_y = tk.DoubleVar(value = 0.)
        self.rotation_z = tk.DoubleVar(value = 0.)
        self.show_orientation = tk.BooleanVar(value = False)
        globals.state_variables.append(self.point_size)
        globals.state_variables.append(self.rotation_x)
        globals.state_variables.append(self.rotation_y)
        globals.state_variables.append(self.rotation_z)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.create_widgets")

        # Point size
        self.point_size_frame = tk.Frame(self)
        self.point_size_label = tk.Label(self.point_size_frame, text="Point size (px)")
        self.point_size_entry = FloatEntry(self.point_size_frame,variable=self.point_size,clamp=(globals.point_size_minimum, None))
        ToolTip.createToolTip(self.point_size_entry, "Point size controls the resolution of the plot. Point sizes < 1 give sub-pixel accuracy but a point size =/= 1 results in data loss. Higher point sizes draw faster. The minimum allowed point size can be modified in globals.py")
        
        # Rotations
        self.rotations_frame = tk.Frame(self)
        self.rotation_label = tk.Label(self.rotations_frame, text="Rotation")
        self.rotation_x_entry = FloatEntry(self.rotations_frame, variable=self.rotation_x, clamp=(0,360),periodic=True)
        self.rotation_y_entry = FloatEntry(self.rotations_frame, variable=self.rotation_y, clamp=(0,360),periodic=True)
        self.rotation_z_entry = FloatEntry(self.rotations_frame, variable=self.rotation_z, clamp=(0,360),periodic=True)

        for widget,hotkey1,hotkey2,axis in zip([self.rotation_x_entry,self.rotation_y_entry,self.rotation_z_entry],['rotate +x','rotate +y','rotate +z'],['rotate -x','rotate -y','rotate -z'],['x','y','z']):
            ToolTip.createToolTip(widget, "Rotate the "+axis+"-axis by the provided Euler angles. Press "+hotkeys_to_string(hotkey1)+" or "+hotkeys_to_string(hotkey2)+" to increment/decrement the "+axis+" angle by "+str(globals.rotation_step)+" degrees (adjustable in globals.py).")

        # Show Orientation
        self.show_orientation_checkbutton = tk.Checkbutton(
            self,
            text="Show orientation",
            variable=self.show_orientation,
            command=self.gui.interactiveplot.orientation.switch_on_off,
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.place_widgets")

        # Point size
        self.point_size_label.pack(side='left')
        self.point_size_entry.pack(side='left',fill='both',expand=True)
        self.point_size_frame.pack(side='top',fill='x',expand=True)
        
        # Rotations
        self.rotation_label.pack(side='left')
        self.rotation_x_entry.pack(side='left',fill='both',expand=True)
        self.rotation_y_entry.pack(side='left',fill='both',expand=True)
        self.rotation_z_entry.pack(side='left',fill='both',expand=True)
        self.rotations_frame.pack(side='top',fill='x',expand=True)

        # Show Orientation
        self.show_orientation_checkbutton.pack(side='top',fill='x',expand=True)

    def create_hotkeys(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.create_hotkeys")
        self.hotkeys = Hotkeys(self.winfo_toplevel())
        self.hotkeys.bind('rotate +x', (
            lambda *args,**kwargs: self.rotation_x.set(self.rotation_x.get()+globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        self.hotkeys.bind('rotate -x', (
            lambda *args,**kwargs: self.rotation_x.set(self.rotation_x.get()-globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        self.hotkeys.bind('rotate +y', (
            lambda *args,**kwargs: self.rotation_y.set(self.rotation_y.get()+globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        self.hotkeys.bind('rotate -y', (
            lambda *args,**kwargs: self.rotation_y.set(self.rotation_y.get()-globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        self.hotkeys.bind('rotate +z', (
            lambda *args,**kwargs: self.rotation_z.set(self.rotation_z.get()+globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        self.hotkeys.bind('rotate -z', (
            lambda *args,**kwargs: self.rotation_z.set(self.rotation_z.get()-globals.rotation_step),
            lambda *args, **kwargs: self.gui.controls.update_button.invoke(),
        ))
        
    def disable_rotations(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.disable_rotations")
        if 'disabled' not in self.rotation_x_entry.state():
            self.rotation_x_entry.state(["disabled"])
            globals.state_variables.remove(self.rotation_x)
            self.rotation_x.set(0)
        if 'disabled' not in self.rotation_y_entry.state():
            self.rotation_y_entry.state(["disabled"])
            globals.state_variables.remove(self.rotation_y)
            self.rotation_y.set(0)
        if 'disabled' not in self.rotation_z_entry.state():
            self.rotation_z_entry.state(["disabled"])
            globals.state_variables.remove(self.rotation_z)
            self.rotation_z.set(0)

    def enable_rotations(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.enable_rotations")
        if 'disabled' in self.rotation_x_entry.state():
            self.rotation_x_entry.state(["!disabled"])
            globals.state_variables.append(self.rotation_x)
        if 'disabled' in self.rotation_y_entry.state():
            self.rotation_y_entry.state(["!disabled"])
            globals.state_variables.append(self.rotation_y)
        if 'disabled' in self.rotation_z_entry.state():
            self.rotation_z_entry.state(["!disabled"])
            globals.state_variables.append(self.rotation_z)
        
    def disable(self,temporarily=False):
        if globals.debug > 1: print("plotcontrols.disable")
        
        children = get_all_children(self)
        if temporarily: self.previous_state = get_widgets_states(children)
        else: self.previous_state = None
        
        set_widgets_states(children,'disabled')

    def enable(self):
        if globals.debug > 1: print("plotcontrols.enable")
        if self.previous_state is not None:
            for widget,state in self.previous_state:
                widget.configure(state=state)
            self.previous_state = None
        else:
            children = get_all_children(self)
            set_widgets_states(children,'normal')
