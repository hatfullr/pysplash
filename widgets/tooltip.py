# https://github.com/matplotlib/matplotlib/blob/1ff14f140546b8df3f17543ff8dac3ddd210c0f1/lib/matplotlib/backends/_backend_tk.py#L840
from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

import globals
import textwrap
import matplotlib.backends

class ToolTip(matplotlib.backends._backend_tk.ToolTip,object):
    after_id = None
    bid = None
    
    @staticmethod
    def createToolTip(widget, text):
        root = widget.winfo_toplevel()
        
        def show(event):
            toolTip.tipwindow.geometry("+%d+%d" % (event.x_root+1,event.y_root+1))
            toolTip.tipwindow.deiconify()
            def command(event):
                toolTip.tipwindow.withdraw()
                if ToolTip.bid is not None:
                    root.unbind("<Motion>", ToolTip.bid)
            ToolTip.bid = root.bind("<Motion>", command, add="+")

        def hide(event):
            toolTip.tipwindow.withdraw()
            if ToolTip.after_id is not None:
                root.after_cancel(ToolTip.after_id)
                ToolTip.after_id = None
               
        def motion(event):
            hide(event)
            if ToolTip.after_id is None:
                ToolTip.after_id = root.after(500, lambda e=event: show(e))
            else:
                root.after_cancel(ToolTip.after_id)
                ToolTip.after_id = None

        text = textwrap.fill(text, width=globals.tooltip_wraplength)
        toolTip = ToolTip(widget)
        toolTip.tipwindow = tk.Toplevel(widget)
        hide(None)
        toolTip.tipwindow.overrideredirect(True)
        try:
            # For Mac OS
            toolTip.tipwindow.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", toolTip.tipwindow._w,
                       "help", "noActivates")
        except tk.TclError:
            pass
        tk.Label(toolTip.tipwindow, text=text, justify='left',relief='solid',borderwidth=1).pack(ipadx=1)
        
        toolTip.tipwindow.bind("<Enter>", hide, add="+")
        toolTip.tipwindow.bind("<Button-1>", lambda *args,**kwargs: print("Button1"), add="+")
        widget.bind("<Motion>", motion, add="+")
        widget.bind("<Leave>", hide, add="+")

