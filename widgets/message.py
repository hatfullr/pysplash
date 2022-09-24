import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
    
# A widget which displays text on top of a frame in some given position

class Message(tk.Label, object):
    def __init__(self, master, anchor, *args, **kwargs):
        self.anchor = anchor
        super(Message,self).__init__(master,*args,**kwargs)
        self.visible = False
        self.show()

    def show(self, *args, **kwargs):
        if not self.visible:
            relxy = (1,1) # se default
            if   self.anchor == "nw"     : relxy = (0  ,   0)
            elif self.anchor == "n"      : relxy = (0.5,   0)
            elif self.anchor == "ne"     : relxy = (1  ,   0)
            elif self.anchor == "w"      : relxy = (0  , 0.5)
            elif self.anchor == "center" : relxy = (0.5, 0.5)
            elif self.anchor == "e"      : relxy = (1  , 0.5)
            elif self.anchor == "sw"     : relxy = (0  ,   1)
            elif self.anchor == "s"      : relxy = (0.5,   1)
            self.place(relx=relxy[0], rely=relxy[1], anchor=self.anchor)
            self.visible = True
        
    def hide(self, *args, **kwargs):
        if self.visible:
            self.place_forget()
            self.visible = False
