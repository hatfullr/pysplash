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
    style_initialized = False
    def __init__(self, master, width=0, *args, **kwargs):
        if not Entry.style_initialized:
            style = ttk.Style()
            style.map(
                "Entry.TEntry",
                fieldbackground=[
                    ('readonly',style.lookup("TEntry", "fieldbackground", state=['!disabled'])),
                    ('disabled',style.lookup("TEntry", "fieldbackground", state=['disabled'])),
                    ('!disabled',style.lookup("TEntry", "fieldbackground", state=['!disabled'])),
                ],
            )
            Entry.style_initialized = True
        
        kwargs['exportselection'] = kwargs.get('exportselection',False)
        kwargs['style'] = kwargs.get('style',"Entry.TEntry")

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

    def configure(self,*args,**kwargs):
        if 'state' in kwargs.keys():
            if kwargs['state'] == 'readonly':
                if 'readonly' not in str(self.cget('state')):
                    self.previous_cursor = self.cget('cursor')
                    kwargs['cursor'] = kwargs.get('cursor', self.master.cget('cursor'))
            else:
                if hasattr(self,"previous_cursor") and self.previous_cursor is not None:
                    kwargs['cursor'] = kwargs.get('cursor', self.previous_cursor)
                    self.previous_cursor = None
                
        return super(Entry,self).configure(*args,**kwargs)
    def config(self,*args,**kwargs):
        return self.configure(*args,**kwargs)
    
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
