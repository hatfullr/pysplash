from functions.getallchildren import get_all_children

def close_window(window):
    # Destroy all the widgets in the application starting from the widgets
    # which have no children, moving up the heirarchy all the way to this
    # root window. This hopefully prevents any Tcl errors that can occur
    # from only using self.destroy()
    for child in get_all_children(window, order_by_level=True):
        # Remove all bindings from the widget so that none of them fire
        # while trying to remove the widget
        child.bindtags(("","","",""))
        child.destroy()
    window.destroy()
