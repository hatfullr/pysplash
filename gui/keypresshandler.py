# This handles keypress events for a Matplotlib
# figure
import globals
class KeyPressHandler:
    def __init__(self,canvas):
        if globals.debug > 1: print("keypresshandler.__init__")
        self.canvas = canvas
        self.cid = None
        self.registrar = {}
        
    def connect(self):
        if globals.debug > 1: print("keypresshandler.connect")
        self.cid = self.canvas.mpl_connect("key_press_event",self.keypress)
        
    def disconnect(self):
        if globals.debug > 1: print("keypresshandler.disconnect")
        self.canvas.mpl_disconnect(self.cid)

    def register(self,key,function,*args,**kwargs):
        if globals.debug > 1: print("keypresshandler.register")
        if key not in self.registrar.keys():
            self.registrar[key] = [function]
        else:
            self.registrar[key] += [function]

    def unregister(self,key,function):
        if globals.debug > 1: print("keypresshandler.unregister")
        if key in self.registrar.keys():
            for r in self.registrar[key]:
                self.registrar[key].remove(r)
                return
                
    def keypress(self,event):
        if globals.debug > 1: print("keypresshandler.keypress")
        # Only process events that happen when the mouse is located
        # within the canvas
        if event.x is not None and event.y is not None:
            if event.key in self.registrar.keys():
                for function in self.registrar[event.key]:
                    function(event)
