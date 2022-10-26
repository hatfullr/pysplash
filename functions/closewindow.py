from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from functions.getallchildren import get_all_children
from lib.tkvariable import save

def close_window(window):
    children = get_all_children(window, order_by_level=True)
    for child in children:
        # Ignore combobox popdown widgets, which we are technically not
        # even supposed to be able to reference
        if 'popdown.f.l' in child._w: continue
        child.event_generate("<<BeforePreferencesSaved>>")
    
    # First save the user's preferences
    save()
    # Destroy all the widgets in the application starting from the widgets
    # which have no children, moving up the heirarchy all the way to this
    # root window. This hopefully prevents any Tcl errors that can occur
    # from only using self.destroy()
    for child in children:
        if 'popdown.f.l' in child._w: continue
        # Remove all bindings from the widget so that none of them fire
        # while trying to remove the widget
        child.bindtags(("","","",""))
        child.destroy()
    window.destroy()
