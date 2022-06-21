from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.font as tkFont

# This custom entry widget automatically expands to fill
# a frame when its width is set to 0.
    
class Entry(ttk.Entry, object):
    def __init__(self, master, width=0, *args, **kwargs):
        kwargs['exportselection'] = kwargs.get('exportselection',False)

        if isinstance(master, (tk.Frame,tk.LabelFrame)):
            super(Entry, self).__init__(master, width=width, *args, **kwargs)
        else:
            self.container = tk.Frame(master)
            super(Entry, self).__init__(self.container, width=width, *args, **kwargs)
            self.pack = lambda *args,**kwargs: self.container.pack(*args,**kwargs)
            self.place = lambda *args,**kwargs: self.container.place(*args,**kwargs)
            self.grid = lambda *args,**kwargs: self.container.grid(*args,**kwargs)
            super(Entry, self).place(relx=0,rely=0,relwidth=1,relheight=1,bordermode="outside")
            self.container.bind("<Map>", self.on_map, add="+")

        bindtags = list(self.bindtags())
        bindtags[2] = ""
        self.bindtags(tuple(bindtags))
        
        # Bind the Enter key to focusout
        self.bind("<Return>", lambda *args,**kwargs: master.focus(), add="+")
        
        # These should be defaults but they aren't for some reason
        self.bind("<FocusOut>", lambda *args,**kwargs: self.select_clear(), add="+")
        self.bind("<FocusIn>", lambda *args,**kwargs: self.select_clear(), add="+")
        
    def on_map(self, *args, **kwargs):
        # If it's 0 do nothing and let the widget auto-fit its surroundings.
        # Otherwise, give it a minimum required width
        width = self.cget('width')
        if width > 0:
            # Measure the width of N characters where N = self.cget('width')
            fontname = str(self.cget('font'))
            if version_info.major < 3: font = tkFont(name=fontname, exists=True)
            else: font = tkFont.nametofont(fontname)

            self.container.configure(width=font.measure("A")*width)
