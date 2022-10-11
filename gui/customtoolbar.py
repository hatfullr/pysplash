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
from functions.configuresubplots import ConfigureSubplots
from gui.interactiveplot import InteractivePlot
import matplotlib
import numpy as np
import sys
import os

class CustomToolbar(NavigationToolbar2Tk):
    matplotlib_default_cursor = matplotlib.backend_tools.Cursors.POINTER
    def __init__(self,master,gui,canvas,**kwargs):
        self.toolitems = (
            (u'Home', u'Reset original view', u'home', u'home'),
            (u'Pan', u'Left button pans, Right button zooms\nx/y fixes axis, CTRL fixes aspect', u'move', u'pan'),
            (u'Zoom', u'Zoom to rectangle\nx/y fixes axis', u'zoom_to_rect', u'zoom'),
            (u'Subplots', u'Configure subplots', u'subplots', u'configure_subplots'),
            (u'Save', u'Save the figure', u'filesave', u'save_figure_as'),
        )
        self.gui = gui
        self.canvas = canvas
        self.toolbar = NavigationToolbar2Tk
        self.toolbar.__init__(self,self.canvas,master)

        # Set the cursor to a + sign when the mouse is inside the axes and
        # a regular pointer arrow when outside the axes
        self.canvas.mpl_connect('axes_enter_event', self.on_axes_enter_event)
        self.canvas.mpl_connect('axes_leave_event', self.on_axes_leave_event)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion_notify_event)
        self._mouse_in_axes = False

        self.queued_zoom = None
        self.zoom_event = None

        self.savename = ""
        self.initialdir = os.getcwd()
        
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
        
        # Press the pan button in the toolbar
        self.mode = matplotlib.backend_bases._Mode.PAN
        self._update_buttons_checked()
        # Set the cursor
        self.set_cursor(matplotlib.backend_tools.Cursors.MOVE)

    def release_pan(self, *args, **kwargs):
        super(CustomToolbar, self).release_pan(*args, **kwargs)
        
        # Update the axis limits in the GUI
        self.update_GUI_axis_limits()

        if self.gui.interactiveplot.isScatterPlot:
            self.gui.controls.update_button.invoke()
        else:
            self.gui.controls.update_button.configure(state='!disabled')

        # Unpress the pan button in the toolbar
        self.mode = matplotlib.backend_bases._Mode.NONE
        self._update_buttons_checked()
        
        # Reset the cursor
        self.set_cursor(InteractivePlot.default_cursor_inside_axes if self._mouse_in_axes else InteractivePlot.default_cursor_outside_axes)
        
    def remove_rubberband(self,event=None):
        # We have to override this function because for some reason it does
        # not work properly in matplotlib
        version = matplotlib.__version__.split(".")
        if int(version[0]) >= 3 and int(version[1]) <= 3:
            self.draw_rubberband(event,0,0,0,0)
        else:
            super(CustomToolbar,self).remove_rubberband()


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
        
        defaultextension = ''
        initialfile = os.path.basename(self.savename) if self.savename else self.canvas.get_default_filename()
        
        savename = tk.filedialog.asksaveasfilename(
            master=self.canvas.get_tk_widget().master,
            title="Save the figure",
            filetypes=tk_filetypes,
            defaultextension=defaultextension,
            initialdir=self.initialdir,
            initialfile=initialfile,
        )
        if not savename: return
        
        self.savename = savename
        self.initialdir = os.path.dirname(self.savename)

        # Save dir for next time
        matplotlib.rcParams['savefig.directory'] = (
            os.path.dirname(str(self.savename)))
        self.save_figure()
            
    def save_figure(self, *args, **kwargs):
        # If we haven't done a "Save As" yet, then do that first
        if not self.savename: self.save_figure_as()

        # If the user didn't specify any name to save, then don't try to save
        if not self.savename: return

        try:
            # This method will handle the delegation to the correct type
            self.canvas.figure.savefig(self.savename)
        except Exception as e:
            tk.messagebox.showerror(master=self.master,title="Error saving file", message=str(e))
        self.gui.message("Figure saved as "+os.path.basename(self.savename))

    def disable(self,*args,**kwargs):
        for child in self.winfo_children():
            child.configure(state='disabled')

    def enable(self,*args,**kwargs):
        for child in self.winfo_children():
            child.configure(state='normal')

    def configure_subplots(self,*args,**kwargs):
        ConfigureSubplots(self.gui)

    def on_motion_notify_event(self, *args, **kwargs):
        if self._mouse_in_axes:
            # If the cursor was previously just the regular cursor, change it to the
            # default inside the axes
            if str(self.canvas.get_tk_widget().cget('cursor')) == matplotlib.backends._backend_tk.cursord[InteractivePlot.default_cursor_outside_axes]:
                self.set_cursor(InteractivePlot.default_cursor_inside_axes)

    def on_axes_enter_event(self, *args, **kwargs):
        self._mouse_in_axes = True
        
    def on_axes_leave_event(self, *args, **kwargs):
        self._mouse_in_axes = False
        # if the cursor was previously the default for inside the axes, change it
        # to the default outside the axes
        if str(self.canvas.get_tk_widget().cget('cursor')) == matplotlib.backends._backend_tk.cursord[InteractivePlot.default_cursor_inside_axes]:
            self.set_cursor(InteractivePlot.default_cursor_outside_axes)
