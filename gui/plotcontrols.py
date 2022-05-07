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
from functions.getwidgetsstates import get_widgets_states
from functions.setwidgetsstates import set_widgets_states
from functions.getallchildren import get_all_children
import globals

class PlotControls(LabelledFrame, object):
    def __init__(self, master, relief='sunken', bd=1, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.__init__")
        super(PlotControls, self).__init__(master, "Plot Controls", *args, relief=relief, bd=bd, **kwargs)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()

    def get_variables(self, *args, **kwargs):
        return [
            self.point_size,
            self.rotation_x,
            self.rotation_y,
            self.rotation_z,
            self.show_orientation,
        ]

    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.create_variables")
        self.point_size = tk.IntVar(value = 1)
        self.rotation_x = tk.DoubleVar(value = 0.)
        self.rotation_y = tk.DoubleVar(value = 0.)
        self.rotation_z = tk.DoubleVar(value = 0.)
        self.show_orientation = tk.BooleanVar(value = False)

    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.create_widgets")

        # Point size
        self.point_size_frame = tk.Frame(self)
        self.point_size_label = tk.Label(self.point_size_frame, text="Point size (px)")
        self.point_size_entry = IntegerEntry(self.point_size_frame,variable=self.point_size,disallowed_values=[0])
        
        # Rotations
        self.rotations_frame = tk.Frame(self)
        self.rotation_label = tk.Label(self.rotations_frame, text="Rotation (x,y,z deg)")
        self.rotation_x_entry = FloatEntry(self.rotations_frame, variable=self.rotation_x)
        self.rotation_y_entry = FloatEntry(self.rotations_frame, variable=self.rotation_y)
        self.rotation_z_entry = FloatEntry(self.rotations_frame, variable=self.rotation_z)

        # Show Orientation
        self.show_orientation_checkbutton = tk.Checkbutton(
            self,
            text="Show orientation",
            variable=self.show_orientation,
        )

    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("plotcontrols.place_widgets")

        # Point size
        self.point_size_label.pack(side='left')
        self.point_size_entry.pack(side='left',fill='x',expand=True)
        self.point_size_frame.pack(side='top',fill='x',expand=True)
        
        # Rotations
        self.rotation_label.pack(side='left')
        self.rotation_x_entry.pack(side='left',fill='x',expand=True)
        self.rotation_y_entry.pack(side='left',fill='x',expand=True)
        self.rotation_z_entry.pack(side='left',fill='x',expand=True)
        self.rotations_frame.pack(side='top',fill='x',expand=True)

        # Show Orientation
        self.show_orientation_checkbutton.pack(side='top',fill='x',expand=True)
        
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
    """
    def set_widget_state(self,widgets,state):
        if globals.debug > 1: print("plotcontrols.set_widget_state")
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
        if globals.debug > 1: print("plotcontrols.get_widget_state")
        if not isinstance(widgets,(list,tuple,np.ndarray)): widgets = [widgets]
        states = []
        for widget in widgets:
            if 'state' in widget.configure():
                if isinstance(widget,tk.Label): continue
                states.append([widget,widget.cget('state')])
        return states
    """
