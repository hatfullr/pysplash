from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk

class ListboxScrollbar(tk.Listbox, object):
    def __init__(self, master, xscrollbar=True, yscrollbar=True, **kwargs):

        self.container = tk.Frame(master)
        super(ListboxScrollbar,self).__init__(self.container,**kwargs)

        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)
        self.grid(row=0,column=0,sticky='news')
        
        if xscrollbar:
            self.xscrollbar = tk.Scrollbar(self.container, orient="horizontal", command=self.xview)
            self.config(xscrollcommand=self.xscrollbar.set)
            self.xscrollbar.grid(row=1,column=0,sticky='ew')
        if yscrollbar:
            self.yscrollbar = tk.Scrollbar(self.container, orient="vertical",command=self.yview)
            self.config(yscrollcommand=self.yscrollbar.set)
            self.yscrollbar.grid(row=0,column=1,sticky='ns')

        self.pack = self.container.pack
        self.grid = self.container.grid
        self.place = self.container.place
