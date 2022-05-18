from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    import tkinter.ttk as ttk
from widgets.mathentry import MathEntry

# This widget allows for the use of either a combobox to select data from
# the gui's data file, or to do a math operation using that same data, such
# as "rho*opacity".

# The problem is that ttk.Combobox does not actually have an entry widget.
# Instead, it itself is basically an entry widget. See the source code here:
# https://fossies.org/linux/tk/library/ttk/combobox.tcl

# All we do is create a MathEntry widget which is invisible to the user. We
# then trace the combobox variable to always update and read from the
# MathEntry variable.
    
class MathCombobox(ttk.Combobox, object):
    def __init__(self, master, gui, *args, **kwargs):
        kwargs['textvariable'] = kwargs.get('textvariable', tk.StringVar())
        textvariable = kwargs['textvariable']
        super(MathCombobox,self).__init__(master,*args,**kwargs)
        self.gui = gui

        mathentrytextvariable = tk.StringVar(value=textvariable.get())
        self.mathentry = MathEntry(self, self.gui, textvariable=textvariable)

        self.mathentry.bind("<FocusOut>", lambda *args,**kwargs: self.event_generate("<<ComboboxSelected>>"), add="+")
        
        self.bind("<Map>", self.on_map, add="+")
        # Make the MathEntry process bindings in the same way as the Combobox's Entry widget,
        # while still retaining the default keybindings inherent to MathEntry widgets.
        bindtags = list(self.bindtags())
        bindtags[0] = self.mathentry
        self.mathentry.bindtags(tuple(bindtags))

    def get(self, *args, **kwargs):
        return self.mathentry.get_data()
        
    def set_entry_size(self, *args, **kwargs):
        self.update_idletasks()

        y = int(0.5*self.winfo_height())
        for x in range(self.winfo_width()):
            result = self.tk.eval('%s identify %d %d' % (self, x, y))
            if result == "downarrow":
                self.mathentry.place(
                    relx=0,
                    rely=0,
                    width=x + self.mathentry.container.cget("borderwidth"),
                    relheight=1,
                )
                break
        else:
            raise RuntimeError("Failed to find the width of the combobox entry")
    
    def on_map(self,event):
        if 'disabled' in self.state(): return
        self.set_entry_size()
        self.bind("<Configure>", self.set_entry_size, add="+")
        

        
