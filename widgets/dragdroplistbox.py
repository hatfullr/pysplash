# https://stackoverflow.com/a/25023944/4954083
from sys import version_info
if version_info.major >= 3: import tkinter as tk
else: import Tkinter as tk

class DragDropListbox(tk.Listbox, object):
    """ A Tkinter listbox with drag'n'drop reordering of entries. """
    def __init__(self, master, **kw):
        kw['selectmode'] = tk.SINGLE
        tk.Listbox.__init__(self, master, **kw)

        def setCurrent(event):
            self.curIndex = self.nearest(event.y)
        def shiftSelection(event):
            i = self.nearest(event.y)
            if i < self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i+1, x)
                self.curIndex = i
                self.event_generate("<<MovedSelected>>")
            elif i > self.curIndex:
                x = self.get(i)
                self.delete(i)
                self.insert(i-1, x)
                self.curIndex = i
                self.event_generate("<<MovedSelected>>")
        
        self.bind('<Button-1>', setCurrent)
        self.bind('<B1-Motion>', shiftSelection)
        self.curIndex = None

    """
    def setCurrent(self, event):
        self.curIndex = self.nearest(event.y)

    def shiftSelection(self, event):
        i = self.nearest(event.y)
        if i < self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i+1, x)
            self.curIndex = i
        elif i > self.curIndex:
            x = self.get(i)
            self.delete(i)
            self.insert(i-1, x)
            self.curIndex = i
    """
