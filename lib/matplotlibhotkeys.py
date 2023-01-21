# This handles keypress events for a Matplotlib
# figure
import globals

# Keyword 'local' means the function will only be called if the user's mouse is hovering
# over the canvas, or if the canvas is in focus. If local is False, then we bind to the
# root widget instead of the canvas.

class MatplotlibHotkeys:
    def __init__(self,canvas):
        if globals.debug > 1: print("matplotlibhotkeys.__init__")
        self.canvas = canvas
        self.registry = []
    
    def register(self,event_type,key,function,local=True):
        if globals.debug > 1: print("matplotlibhotkeys.register")

        togive = {
            'event_type':event_type,
            'key':key,
            'function':function,
            'local':local,
            'id':None,
        }

        if local:
            togive['id'] = self.canvas.mpl_connect(event_type, lambda event: self.process_local_event(togive,event))
        else:
            togive['id'] = self.canvas.get_tk_widget().winfo_toplevel().bind(event_type, lambda event: self.process_event(event_type,togive, event), add="+")

        self.registry.append(togive)

    def process_local_event(self, obj, event):
        if globals.debug > 1: print("matplotlibhotkeys.process_local_event")
        if event.x is None and event.y is None: return
        if event.key == obj['key']: obj['function'](event)

    def process_event(self, event_type, obj, event):
        if globals.debug > 1: print("matplotlibhotkeys.process_event")
        #if event_type == "KeyPress":
        #    print(event)
        
        
