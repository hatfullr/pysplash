from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk
import globals
import numpy as np

def set_widgets_states(widgets,state):
    if globals.debug > 1: print("set_widgets_states")
    if not isinstance(widgets,(list,tuple,np.ndarray)): widgets = [widgets]
    for widget in widgets:
        if isinstance(widget,(tk.Label, ttk.Label)): continue
        # tk widgets, and also ttk.Combobox
        if hasattr(widget, 'configure') and widget.configure():
            if 'state' in widget.configure().keys():
                current_state = widget.cget('state')
                if current_state != state:
                    if isinstance(widget,ttk.Combobox):
                        if state == 'normal': widget.configure(state='readonly')
                    else:
                        widget.configure(state=state)
        # ttk widgets
        elif hasattr(widget, 'state'):
            current_state = widget.state()
            mystate = state
            if isinstance(mystate, str):
                if mystate == 'normal': mystate = '!disabled'
                widget.state([mystate])
            elif isinstance(mystate, (list, tuple, np.ndarray)):
                if not any([s in current_state for s in mystate]):
                    widget.state(mystate)
            else:
                raise TypeError("Unrecognized state type '"+type(mystate).__name__+"'. Expected one of 'str', 'list', 'tuple', or 'np.ndarray'")
