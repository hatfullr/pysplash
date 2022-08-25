import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    import ttk
    from tkFont import Font as tkFont
else:
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkinter.font as tkFont
from widgets.button import Button
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.collections import PathCollection
from functions.hotkeystostring import hotkeys_to_string
import matplotlib
import numpy as np
import sys
import os

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self,master,gui,canvas,**kwargs):
        self.toolitems = (
            (u'Home', u'Reset original view', u'home', u'home'),
            (u'Pan', u'Left button pans, Right button zooms\nx/y fixes axis, CTRL fixes aspect', u'move', u'pan'),
            (u'Zoom', u'Zoom to rectangle\nx/y fixes axis', u'zoom_to_rect', u'zoom'),
            (u'Subplots', u'Configure subplots', u'subplots', u'configure_subplots'),
            (u'Save', u'Save the figure '+hotkeys_to_string('save'), u'filesave', u'save_figure'),
        )
        self.gui = gui
        self.canvas = canvas
        self.toolbar = NavigationToolbar2Tk
        self.toolbar.__init__(self,self.canvas,master)

        self.queued_zoom = None
        self.zoom_event = None

        self.savename = ""
        
        self.configure(**kwargs)

        # Remove the "x=... y=..." labels
        for child in self.winfo_children():
            if isinstance(child, tk.Label):
                child.destroy()

        self.toolbar.set_message = self.set_xy_message

    def home(self,*args,**kwargs):
        # Turn off adaptive limits on the X and Y axes
        # Reset the view
        self.gui.interactiveplot.clear_tracking()
        self.gui.interactiveplot.origin = np.zeros(2)
        self.gui.interactiveplot.reset_xylim()

        # Update the axis limits in the GUI
        self.update_GUI_axis_limits()
        
        # Update the plot
        self.gui.controls.update_button.invoke()
        
    def get_home_xylimits(self, *args, **kwargs):
        # Simulate a Home button press, but without drawing the plot. Return
        # the resulting x-y limits as xmin, xmax, ymin, ymax
        # https://github.com/matplotlib/matplotlib/blob/223b2b13d67f0be0e64898b9d3ca191f56dc6f82/lib/matplotlib/backend_bases.py
        # https://github.com/matplotlib/matplotlib/blob/c6c7ec1978c22ae2c704555a873d0ec6e1e2eaa8/lib/matplotlib/axes/_base.py
        self._nav_stack.home()
        self.set_history_buttons()
        nav_info = self._nav_stack()
        if nav_info is not None:
            # Retrieve all items at once to avoid any risk of GC deleting an Axes
            # while in the middle of the loop below.
            items = list(nav_info.items())
            for ax, (view, (pos_orig, pos_active)) in items:
                if ax is self.gui.interactiveplot.ax:
                    return view
        return None, None, None, None
        
    def set_xy_message(self, *args, **kwargs):
        if sys.version_info.major < 3: types = (str,unicode)
        else: types = str
        for arg in args:
            if isinstance(arg, types):
                self.gui.interactiveplot.xycoords.set(arg)
                break
        else:
            self.gui.interactiveplot.xycoords.set("")

    def on_queued_zoom(self):
        flag = False
        if self.gui.interactiveplot.drawn_object is not None: flag = True

        #if flag: self.gui.interactiveplot.drawn_object._disconnect()
            
        super(CustomToolbar,self).release_zoom(self.zoom_event)
        
        #if flag: self.gui.interactiveplot.drawn_object._connect()
        
        # Clear the zoom event after we have completed the zoom
        self.zoom_event = None
        self.queued_zoom = None

        # Update the axis limits in the GUI
        self.update_GUI_axis_limits()

    def cancel_queued_zoom(self, *args, **kwargs):
        self.remove_rubberband()
        # Cancel a queued zoom
        if self.queued_zoom:
            # Remove the zoom information
            self._zoom_info = None
            # Fire the zoom event to trick Matplotlib into removing the rubberband
            self.queued_zoom()

    def update_GUI_axis_limits(self, *args, **kwargs):
        for axis_controller in self.gui.controls.axis_controllers.values():
            axis_controller.limits.on_axis_limits_changed()
            axis_controller.limits.adaptive_off()
            
    def release_zoom(self,event):
        self.queued_zoom = None
        if sys.version_info.major < 3: # Python2
            for zoom_id in self._ids_zoom:
                self.canvas.mpl_disconnect(zoom_id)
            self.zoom_event = event
            self.queued_zoom = self.on_queued_zoom
        else: # Python3
            if self._zoom_info is not None:
                if isinstance(self._zoom_info,dict):
                    axes = self._zoom_info['axes']
                    cid = self._zoom_info['cid']
                elif hasattr(self._zoom_info,'axes'):
                    axes = self._zoom_info.axes
                    cid = self._zoom_info.cid
                else:
                    raise ValueError("Problem with the matplotlib zoom function. Please submit a bug report on GitHub with your current version of matplotlib.")
                self.canvas.mpl_disconnect(cid)
                self.zoom_event = event
                self.queued_zoom = self.on_queued_zoom
        if self.queued_zoom is not None:
            #self.gui.controls.save_state()
            self.gui.controls.on_state_change()

    def press_pan(self,*args,**kwargs):
        self.cancel_queued_zoom()
        super(CustomToolbar,self).press_pan(*args,**kwargs)
            
    def release_pan(self, *args, **kwargs):
        super(CustomToolbar, self).release_pan(*args, **kwargs)

        # Update the axis limits in the GUI
        self.update_GUI_axis_limits()

        self.gui.controls.update_button.invoke()
        
    def remove_rubberband(self,event=None):
        # We have to override this function because for some reason it does
        # not work properly in matplotlib
        version = matplotlib.__version__.split(".")
        if int(version[0]) >= 3 and int(version[1]) <= 3:
            self.draw_rubberband(event,0,0,0,0)


# https://github.com/matplotlib/matplotlib/blob/1ff14f140546b8df3f17543ff8dac3ddd210c0f1/lib/matplotlib/backends/_backend_tk.py#L782
            
    def save_figure_as(self, *args, **kwargs):
        filetypes = self.canvas.get_supported_filetypes().copy()
        default_filetype = self.canvas.get_default_filetype()

        # Tk doesn't provide a way to choose a default filetype,
        # so we just have to put it first
        default_filetype_name = filetypes.pop(default_filetype)
        sorted_filetypes = ([(default_filetype, default_filetype_name)]
                            + sorted(filetypes.items()))
        tk_filetypes = [(name, '*.%s' % ext) for ext, name in sorted_filetypes]
        
        # adding a default extension seems to break the
        # asksaveasfilename dialog when you choose various save types
        # from the dropdown.  Passing in the empty string seems to
        # work - JDH!
        # defaultextension = self.canvas.get_default_filetype()
        defaultextension = ''
        initialfile = self.canvas.get_default_filename()
        
        self.savename = tk.filedialog.asksaveasfilename(
            master=self.canvas.get_tk_widget().master,
            title="Save the figure",
            filetypes=tk_filetypes,
            defaultextension=defaultextension,
            initialdir=os.getcwd(),
            initialfile=initialfile,
        )

        if self.savename in ["",()]: return

        # Save dir for next time
        matplotlib.rcParams['savefig.directory'] = (
            os.path.dirname(str(self.savename)))
        self.save_figure()
            
    def save_figure(self, *args, **kwargs):
        # If we haven't done a "Save As" yet, then do that first
        if self.savename in ["", ()]: self.save_figure_as()

        try:
            # This method will handle the delegation to the correct type
            self.canvas.figure.savefig(self.savename)
            self.gui.message("Figure saved as "+os.path.basename(self.savename))
        except Exception as e:
            tk.messagebox.showerror(master=self.master,title="Error saving file", message=str(e))
