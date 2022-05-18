from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    from tkinter import ttk
    import tkinter.font as tkFont
from widgets.entry import Entry
    
class FlashingEntry(Entry,object):
    def __init__(self,master,borderwidth=1,flash_color='red',**kwargs):
        self._flash_after_id = None
        self.flash_color = flash_color
        self.flashing = False

        self.container = tk.Frame(master,borderwidth=1)
        super(FlashingEntry, self).__init__(self.container,**kwargs)
        super(FlashingEntry, self).place(relx=0,rely=0,relwidth=1,relheight=1,bordermode="outside")
        
        self.pack = lambda *args,**kwargs: self.container.pack(*args,**kwargs)
        self.place = lambda *args,**kwargs: self.container.place(*args,**kwargs)
        self.grid = lambda *args,**kwargs: self.container.grid(*args,**kwargs)

        self.previous_style = None
        self.container.bind("<Map>", self.on_map, add="+")

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
        
    def flash(self,time=1000):
        if not self.flashing:
            self.flashing = True
            self.previous_style = {
                'background':self.container.cget('background'),
            }
            self.container.configure(background=self.flash_color)
            # Set the focus to this widget
            self.focus()
        else:
            # We are already flashing, so we should extend the flash duration
            # such that the flashing ends "time" from now
            if self._flash_after_id is not None:
                self.after_cancel(self._flash_after_id)
        self._flash_after_id = self.after(time,self._stop_flash)
    
    def _stop_flash(self,*args,**kwargs):
        if self._flash_after_id is not None:
            self.after_cancel(self._flash_after_id)
        self._flash_after_id = None
        if self.previous_style is not None: self.container.configure(self.previous_style)
        self.flashing = False


