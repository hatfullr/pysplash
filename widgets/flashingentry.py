from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk
from widgets.entry import Entry
    
class FlashingEntry(Entry,object):
    def __init__(self,master,borderwidth=1,flash_color='red',**kwargs):
        self._flash_after_id = None
        self.flash_color = flash_color
        self.flashing = False

        self.container = tk.Frame(master,borderwidth=1)
        super(FlashingEntry, self).__init__(self.container,**kwargs)
        super(FlashingEntry, self).pack(fill='both',expand=True)
        
        self.pack = lambda *args,**kwargs: self.container.pack(*args,**kwargs)
        self.place = lambda *args,**kwargs: self.container.place(*args,**kwargs)
        self.grid = lambda *args,**kwargs: self.container.grid(*args,**kwargs)

        self.previous_style = None

    def destroy(self, *args, **kwargs):
        if self._flash_after_id is not None: self.after_cancel(self._flash_after_id)
        super(FlashingEntry,self).destroy(*args,**kwargs)

    def flash(self,time=1000):
        # Set the focus to this widget
        self.focus()
        
        if not self.flashing:
            self.flashing = True
            self.previous_style = {
                'background':self.container.cget('background'),
            }
            self.container.configure(background=self.flash_color)
        else:
            # We are already flashing, so we should extend the flash duration
            # such that the flashing ends "time" from now
            if self._flash_after_id is not None:
                self.after_cancel(self._flash_after_id)
        self._flash_after_id = self.after(time,self._stop_flash)
        return "break"
    
    def _stop_flash(self,*args,**kwargs):
        if self._flash_after_id is not None:
            self.after_cancel(self._flash_after_id)
        self._flash_after_id = None
        if self.previous_style is not None: self.container.configure(self.previous_style)
        self.flashing = False


