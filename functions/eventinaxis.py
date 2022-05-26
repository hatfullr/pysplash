from functions.tkeventtomatplotlibmouseevent import tkevent_to_matplotlibmouseevent

# This method returns True when the provided event is positioned inside the
# plotted axis object, such as the user's mouse position.
def event_in_axis(axis, event):
    if event.widget is not axis.get_figure().canvas.get_tk_widget(): return False
    event = tkevent_to_matplotlibmouseevent(axis, event)
    #print(event.inaxes)
    return event.inaxes is not None
