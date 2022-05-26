from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk


# https://stackoverflow.com/a/37861801/4954083

class VerticalScrolledFrame(tk.Frame, object):
    """
    1. Master widget gets scrollbars and a canvas. Scrollbars are connected 
    to canvas scrollregion.

    2. self.interior is created and inserted into canvas

    Usage Guideline:
    Assign any widgets as children of <ScrolledWindow instance>.interior
    to get them inserted into canvas
    """
    def __init__(self, master, *args, **kwargs):
        self.master = master
        super(VerticalScrolledFrame,self).__init__(self.master, *args, **kwargs)
        
        self.root = self.winfo_toplevel()

        bg = kwargs.get('background',kwargs.get('bg',ttk.Style().lookup('TFrame','background')))
        
        # creating a canvas
        self.canv = tk.Canvas(
            self,
            borderwidth=0,
            highlightthickness=0,
            background=bg,
            name='canvas',
        )
        
        # creating a frame to insert to canvas
        self.interior = tk.Frame(
            self.canv,
            borderwidth=0,
            highlightthickness=0,
            background=bg,
            name='interior',
        )
        self.yscrlbr = ttk.Scrollbar(self,name='yscrlbr')
        
        self.yscrlbr.config(command = self.canv.yview)
        self.interior_id = self.canv.create_window(0, 0, window = self.interior, anchor = 'nw')
        self.canv.config(yscrollcommand = self.yscrlbr.set)
        
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        
        self.yscrlbr.grid(column = 1, row = 0, sticky = 'nes')
        self.canv.grid(column = 0, row = 0, sticky = 'news')

        self.canv.bind('<Configure>', self._configure_canvas)
        self.interior.bind('<Configure>', self._configure_interior)
        self.bind('<Enter>', self._on_Enter)
        self.bind('<Leave>', self._on_Leave)

        self.bind_buttons = ['<MouseWheel>','<Button-4>','<Button-5>']
        
    def _on_Enter(self, event):
        for button in self.bind_buttons:
            self.canv.bind_all(button,self._on_mousewheel)
        self.yscrlbr.bind("<B1-Motion>",self._on_B1Motion)
    
    def _on_Leave(self, event):
        for button in self.bind_buttons:
            self.canv.unbind_all(button)
        self.yscrlbr.unbind("<B1-Motion>")

    def _on_B1Motion(self, event):
        if self.yscrlbr.get() == (0.0,1.0): return "break"
            
    def _on_mousewheel(self, event):
        if event.num in [4,5]: # Linux
            if event.num == 5:
                self._scroll(1,'units')
            elif event.num == 4:
                self._scroll(-1,'units')
        else: # Windows
            self._scroll(int(-1*(event.delta/120)), "units")

    def _scroll(self,amount,units):
        if self.yscrlbr.get() != (0.0,1.0):
            self.canv.yview_scroll(amount,units)
            
    def _configure_interior(self, event):
        # update the scrollbars to match the size of the inner frame
        size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
        self.canv.config(scrollregion='0 0 %s %s' % size)
        if size[0] != self.canv.winfo_width():
            self.canv.config(width=size[0])
    
    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self.canv.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canv.itemconfigure(self.interior_id, width=self.canv.winfo_width())
    
