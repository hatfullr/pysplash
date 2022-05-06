from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

# This custom entry widget automatically expands to fill
# a frame when its width is set to 0.
    
class Entry(ttk.Entry, object):
    def __init__(self, master, width=0, *args, **kwargs):

        if isinstance(master, (tk.Frame,tk.LabelFrame)):
            super(Entry, self).__init__(master, width=width, *args, **kwargs)
        else:
            self.container = tk.Frame(master)
            super(Entry, self).__init__(self.container, width=width, *args, **kwargs)
            self.pack = lambda *args,**kwargs: self.container.pack(*args,**kwargs)
            self.place = lambda *args,**kwargs: self.container.place(*args,**kwargs)
            self.grid = lambda *args,**kwargs: self.container.grid(*args,**kwargs)
            super(Entry,self).pack(fill='both')

        # Bind the Enter key to focusout
        self.bind("<Return>", lambda *args,**kwargs: self.winfo_toplevel().focus())
