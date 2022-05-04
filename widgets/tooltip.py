# https://github.com/matplotlib/matplotlib/blob/1ff14f140546b8df3f17543ff8dac3ddd210c0f1/lib/matplotlib/backends/_backend_tk.py#L840
import globals
import textwrap
import matplotlib.backends

class ToolTip(matplotlib.backends._backend_tk.ToolTip,object):
    @staticmethod
    def createToolTip(widget, text):
        text = textwrap.fill(text, width=globals.tooltip_wraplength)
        toolTip = ToolTip(widget)
        def enter(event):
            toolTip.showtip(text)
            # ttk widgets have an attribute called "state" which they use
            # to set the widget styling. When the user is hovering over
            # the widget, we should make sure the widget's style is set
            # to the "active" state
            if hasattr(widget, "state") and widget.state() != 'disabled':
                widget.state(['active'])
        def leave(event):
            toolTip.hidetip()
            if hasattr(widget, "state") and widget.state() != 'disabled':
                widget.state(["!active"])
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
