from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

class LabelledFrame(tk.Frame,object):
    def __init__(self,master,text,*args,**kwargs):
        self.init = True
        self.master = master
        self.container = tk.Frame(self.master)
        super(LabelledFrame,self).__init__(self.container,*args,**kwargs)
        
        self.container.columnconfigure(0,weight=1)
        self.container.rowconfigure(0,weight=1)
        
        self._label = tk.Label(self.container,text=text,anchor='nw',font='TkDefault 12 bold')

        self._label.pack(side='top',fill='x',anchor='nw')
        self.pack(side='top',expand=True,fill='both')
        self.init = False

    def pack(self,*args,**kwargs):
        if self.init: return super(LabelledFrame,self).pack(*args,**kwargs)
        else: return self.container.pack(*args,**kwargs)
    def grid(self,*args,**kwargs):
        if self.init: return super(LabelledFrame,self).grid(*args,**kwargs)
        else: return self.container.grid(*args,**kwargs)
    def place(self,*args,**kwargs):
        if self.init: return super(LabelledFrame,self).place(*args,**kwargs)
        else: return self.container.place(*args,**kwargs)
            
