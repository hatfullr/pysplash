import types
import inspect

permanent_state_widgets = {}

def set_widget_state_permanent(widget, state):
    if str(widget) not in permanent_state_widgets.keys():
        
        widget.configure(state=state)
        
        def new_configure(event):
            widget = permanent_state_widgets[str(event.widget)]['widget']
            widget.unbind("<Configure>", permanent_state_widgets[str(widget)]['bind id'])
            widget.configure(state=permanent_state_widgets[str(widget)]['state'])
            permanent_state_widgets[str(widget)]['bind id'] = widget.bind("<Configure>", new_configure, add="+")

        permanent_state_widgets[str(widget)] = {
            'widget' : widget,
            'bind id' :  widget.bind("<Configure>", new_configure, add="+"),
            'state' : state,
        }
        

def release_widget_state_permanent(widget):
    if str(widget) in permanent_state_widgets.keys():
        permanent_state_widgets[str(widget)]['widget'].unbind("<Configure>", permanent_state_widgets[str(widget)]['bind id'])
        permanent_state_widgets.pop(str(widget))
