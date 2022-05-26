from matplotlib.backend_bases import MouseEvent

# Convert a tkinter event into a matplotlib event. That is,
def tkevent_to_matplotlibmouseevent(axis,tkevent):
    # Convert the given event into a Matplotlib MouseEvent
    if tkevent.num == 5 or tkevent.delta < 0: button = "down"
    elif tkevent.num == 4 or tkevent.delta > 0: button = "up"
    else: button = 1 # Fake a left click
    
    # Kinda silly that we have to do this, but at least it works.
    return MouseEvent("zoom", axis.get_figure().canvas, tkevent.x, tkevent.y, button=button)
