from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

class ProgressBar(ttk.Progressbar,object):
    def __init__(self,master,textvariable=None,**kwargs):
        self.container = tk.Frame(master)
        
        super(ProgressBar,self).__init__(self.container,**kwargs)

        self.label = tk.Label(self.container)

        super(ProgressBar,self).pack(side='top',fill='both',expand=True)
        self.label.pack(side='top',fill='x',expand=True)

    def pack(self,*args,**kwargs):
        self.container.pack(*args,**kwargs)
    def grid(self,*args,**kwargs):
        self.container.grid(*args,**kwargs)
    def place(self,*args,**kwargs):
        self.container.place(*args,**kwargs)

    def set_text(self,new_text):
        self.label.configure(text=new_text)
