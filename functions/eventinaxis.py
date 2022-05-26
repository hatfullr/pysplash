# This method returns True when the provided event is positioned inside the
# plotted axis object, such as the user's mouse position.
def event_in_axis(axis, event):
    canvas = axis.get_figure().canvas
    widget = canvas.get_tk_widget()
    
    mousex = event.x_root
    mousey = widget.winfo_screenheight() - event.y_root

    # Check to see if the mouse is hovering over the axis. If it isn't, then don't do anything.
    # First get the canvas widget's size
    x0 = widget.winfo_rootx()
    y0 = widget.winfo_rooty()
    x1 = x0 + widget.winfo_width()
    y1 = y0 + widget.winfo_height()

    # Use the canvas widget's size to get the position of the axis
    pos = axis.get_position()
    axwidth = pos.width * (x1-x0)
    axheight = pos.height * (y1-y0)
    ax_x0 = x0 + axwidth*pos.x0
    ax_x1 = ax_x0 + axwidth
    ax_y0 = y0 + axheight*pos.y0
    ax_y1 = ax_y0 + axheight

    if ((ax_x0 <= mousex and mousex <= ax_x1) and
        (ax_y0 <= mousey and mousey <= ax_y1)):
        return True
    return False
