from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

class FlashingEntry(ttk.Entry,object):
    def __init__(self,master,borderwidth=1,flash_color='red',**kwargs):
        self._flash_after_id = None
        self.flash_color = flash_color
        self.flashing = False
        
        self.container = tk.Frame(master,borderwidth=borderwidth)
        super(FlashingEntry,self).__init__(self.container,**kwargs)
        super(FlashingEntry,self).pack(expand=True,fill='both')

    def pack(self,*args,**kwargs):
        self.container.pack(*args,**kwargs)

    def place(self,*args,**kwargs):
        self.container.place(*args,**kwargs)

    def grid(self,*args,**kwargs):
        self.container.grid(*args,**kwargs)

    def flash(self,time=1000):
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
    
    def _stop_flash(self,*args,**kwargs):
        self._flash_after_id = None
        self.container.configure(self.previous_style)
        self.flashing = False


