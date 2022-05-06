from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import globals
import numpy as np

def get_widgets_states(widgets):
    if globals.debug > 1: print("get_widgets_states")

    if not isinstance(widgets,(list,tuple,np.ndarray)): widgets = [widgets]
    states = []
    for widget in widgets:
        # tk widgets
        if hasattr(widget,'configure') and widget.configure():
            if 'state' in widget.configure().keys():
                states.append([widget,widget.cget('state')])
        # ttk widgets
        elif hasattr(widget, 'state'):
            states.append([widget,widget.state()])
    return states
