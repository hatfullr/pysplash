from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import globals

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection, PolyCollection
import matplotlib.backend_bases
import matplotlib.colorbar
import matplotlib.colors
import numpy as np
from copy import copy
import collections

from gui.customcanvas import CustomCanvas

from lib.hotkeys import Hotkeys
from lib.scatterplot import ScatterPlot
from lib.integratedvalueplot import IntegratedValuePlot
from lib.orientationarrows import OrientationArrows
from lib.customaxesimage import CustomAxesImage
from lib.customcolorbar import CustomColorbar
from lib.pointdensityplot import PointDensityPlot
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar

from functions.findnearest2d import find_nearest_2d
from functions.stringtofloat import string_to_float
from functions.eventinaxis import event_in_axis
from functions.tkeventtomatplotlibmouseevent import tkevent_to_matplotlibmouseevent
from functions.getallchildren import get_all_children

from widgets.resizableframe import ResizableFrame

import warnings
import inspect
import traceback

class InteractivePlot(ResizableFrame,object):
    def __init__(self,master,gui,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.__init__")
        self.gui = gui

        super(InteractivePlot,self).__init__(master,*args,**kwargs)

        self.fig = Figure(figsize=(6,6),dpi=int(self.gui.dpi))
        self.ax = self.fig.add_subplot(111)

        self.x_cid = None
        self.y_cid = None

        self.orientation = OrientationArrows(self.gui,self.ax)
        
        self.colorbar = CustomColorbar(self.ax)

        self.drawn_object = None
        self.previously_drawn_object = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        self.create_hotkeys()
        
        self.previous_args = None
        self.previous_kwargs = None
        self.previous_xlim = None
        self.previous_ylim = None

        self.origin = np.zeros(2)
        self.origin_cid = None
        self.track_id = None
        self.colors = None

        self._select_info = None

        self.selection = None

        self.particle_annotation_cid = None
        self.particle_annotation = self.ax.text(0,0,"")
        self.track_and_annotate = False

        # If the user clicks anywhere on the plot, focus the plot.
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda *args, **kwargs: self.canvas.get_tk_widget().focus_set(), add="+")

        self._id_select_press = self.canvas.mpl_connect('button_press_event', self.press_select)
        self._id_select_release = self.canvas.mpl_connect('button_release_event', self.release_select)

        self.mouse = np.array([None,None])
        self.canvas.mpl_connect("axes_leave_event", self.clear_mouse)
        self.canvas.mpl_connect("motion_notify_event", self.update_mouse)
            
        self.bind = lambda *args, **kwargs: self.canvas.get_tk_widget().bind(*args,**kwargs)
        self.unbind = lambda *args, **kwargs: self.canvas.get_tk_widget().unbind(*args,**kwargs)

        self._after_id_update = None

        # Apply the style given in the user's preferences
        #style = self.gui.preferences["style"]
        #if style is not None: self.set_style(style)

    def create_variables(self):
        if globals.debug > 1: print("interactiveplot.create_variables")
        self.xycoords = tk.StringVar()
        self.time = DoubleVar(self,None,'time')
        
        self.time.trace('w',lambda *args, **kwargs: self.set_time_text())

        self.time_text = None
    
    def create_widgets(self):
        if globals.debug > 1: print("interactiveplot.create_widgets")
        #self.canvas = CustomCanvas(self.fig, master=self)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.xycoords_label = tk.Label(self,textvariable=self.xycoords,bg='white')

    def create_hotkeys(self):
        if globals.debug > 1: print("interactiveplot.create_hotkeys")
        self.hotkeys = Hotkeys(self.canvas.get_tk_widget().winfo_toplevel())
        self.hotkeys.bind("start pan", self.start_pan)
        self.hotkeys.bind("drag pan", self.drag_pan)
        self.hotkeys.bind("stop pan", self.stop_pan)
        self.hotkeys.bind("zoom", self.zoom)
        self.hotkeys.bind("zoom x", lambda event: self.zoom(event, which='x'))
        self.hotkeys.bind("zoom y", lambda event: self.zoom(event, which='y'))
        self.hotkeys.bind("track particle", lambda event: self.track_particle(event))
        self.hotkeys.bind("track and annotate particle", (
            lambda event: self.track_particle(event),
            lambda event: self.annotate_tracked_particle(event),
        ))
        self.hotkeys.bind("annotate time", lambda event: self.set_time_text(event))
        for i in range(10):
            self.hotkeys.bind("particle color "+str(i), self.color_particles)
            
    def destroy(self, *args, **kwargs):
        if self._after_id_update is not None: self.after_cancel(self._after_id_update)
        # The artists we drew onto the plot need to be removed so that
        # their "after" methods get cancelled properly before we
        # destroy this widget
        if (self.drawn_object is not None and
            self.drawn_object in self.ax.get_children()):
            #if self.drawn_object in self.canvas.blit_artists:
            #    self.canvas.blit_artists.remove(self.drawn_object)
            self.drawn_object.remove()
        if (self.previously_drawn_object is not None and
            self.previously_drawn_object in self.ax.get_children()):
            self.previously_drawn_object.remove()
        
    def place_widgets(self):
        if globals.debug > 1: print("interactiveplot.place_widgets")
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.xycoords_label.place(in_=self.canvas.get_tk_widget(),relx=1,rely=1,anchor='se')

    def update_mouse(self, event):
        self.mouse = np.array([event.xdata,event.ydata])
    def clear_mouse(self, event):
        self.mouse = np.array([None,None])

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.reset")
        if self.drawn_object is not None:
            #if self.drawn_object in self.canvas.blit_artists:
            #    self.canvas.blit_artists.remove(self.drawn_object)
            self.drawn_object.remove()
            self.drawn_object = None
        self.reset_colors()

    def reset_colors(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.reset_colors")
        self.colors = None
        
    def update(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update")
        # If we are waiting to update, then make sure the controls' update button is disabled
        #self.gui.controls.update_button.state(['disabled'])
        if globals.plot_update_delay > 0:
            if self._after_id_update is not None:
                self.after_cancel(self._after_id_update)
            self._after_id_update = self.after(globals.plot_update_delay, self._update)
        else: self._update()
    
    def _update(self,*args, **kwargs):
        if globals.debug > 1:
            print("interactiveplot._update")
            print("    self.ax = ",self.ax)

        if self._after_id_update is not None:
            self.after_cancel(self._after_id_update)
            self._after_id_update = None

        #self.reset()

        # Stale the axis controllers before fetching their data, so that we
        # obtain fresh data
        for axis_controller in self.gui.controls.axis_controllers.values():
            axis_controller.stale = True

        xaxis = self.gui.controls.axis_controllers['XAxis']
        yaxis = self.gui.controls.axis_controllers['YAxis']
        x, x_display_units, x_physical_units = xaxis.data, xaxis.display_units, xaxis.physical_units
        y, y_display_units, y_physical_units = yaxis.data, yaxis.display_units, yaxis.physical_units

        # Don't try to plot anything if there's no data to plot
        if x is None or y is None: return

        self.origin = np.zeros(2)
        if self.track_id is not None and self.track_id in np.arange(len(x)):
            self.origin = np.array([x[self.track_id],y[self.track_id]])

        if self.colors is None:
            if isinstance(x, (np.ndarray, list, tuple)):
                self.colors = np.ones(len(x))
            else:
                self.colors = np.ones(1)

        if (xaxis.value.get() in ['x','y','z'] and
            yaxis.value.get() in ['x','y','z']):
            aspect = 'equal'
        else:
            aspect = None

        # If there's no data to plot, stop here
        if not self.gui.data:
            self.after_calculate()
            return

        
        kwargs = {}
        colorbar_text = self.gui.controls.axis_controllers['Colorbar'].value.get()
        
        # Scatter plot
        if colorbar_text.strip() in ['None',None,'']:
            if self.gui.data.is_image:
                method = CustomAxesImage
                args = (
                    self.ax,
                    self.gui.data,
                )
                kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
                kwargs['aspect'] = aspect
                self.colorbar.show()
            else:
                method = ScatterPlot
                args = (
                    self.ax,
                    x,
                    y,
                )
                kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
                kwargs['c'] = self.colors
                kwargs['aspect'] = aspect
                kwargs['aftercalculate'] = self.after_scatter_calculate

                if self.track_id is not None:
                    xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
                    dx = 0.5*(xlim[1]-xlim[0])
                    dy = 0.5*(ylim[1]-ylim[0])
                    xlim = (self.origin[0]-dx,self.origin[0]+dx)
                    ylim = (self.origin[1]-dy,self.origin[1]+dy)
                    self.ax.set_xlim(xlim)
                    self.ax.set_ylim(ylim)
                    xaxis.limits.set_limits(xlim)
                    yaxis.limits.set_limits(ylim)
                
                self.colorbar.hide()

        elif colorbar_text.strip() == 'Point Density':
            method = PointDensityPlot
            args = (
                self.ax,
                x,
                y,
            )
            
            kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
            kwargs['aspect'] = aspect
            kwargs['aftercalculate'] = self.after_scatter_calculate
            kwargs['cmap'] = self.colorbar.cmap
            kwargs['cscale'] = self.gui.controls.axis_controllers['Colorbar'].scale.get()
            kwargs['cunits'] = self.gui.controls.axis_controllers['Colorbar'].units.value.get()
            kwargs['colorbar'] = self.colorbar
                
            self.colorbar.show()
        else:
            caxis = self.gui.controls.axis_controllers['Colorbar']
            A, A_display_units, A_physical_units = caxis.data, caxis.display_units, caxis.physical_units
            if A is None or A_display_units is None or A_physical_units is None:
                raise Exception("One of A, A_display_units, or A_physical_units was None. This should never happen.")
            
            m = self.gui.get_display_data('m')
            h = self.gui.get_display_data('h')
            rho = self.gui.get_display_data('rho')

            idx = self.gui.get_data('u') != 0

            method = IntegratedValuePlot
            args = (
                self.ax,
                A[idx],
                x[idx],
                y[idx],
                m[idx],
                h[idx],
                rho[idx],
                [ # physical units
                    A_physical_units,
                    x_physical_units,
                    y_physical_units,
                    self.gui.get_physical_units('m'),
                    self.gui.get_physical_units('h'),
                    self.gui.get_physical_units('rho'),
                ],
                [ # display units
                    A_display_units,
                    x_display_units,
                    y_display_units,
                    self.gui.get_display_units('m'),
                    self.gui.get_display_units('h'),
                    self.gui.get_display_units('rho'),
                ],
            )

            kwargs['cmap'] = self.colorbar.cmap
            kwargs['cscale'] = self.gui.controls.axis_controllers['Colorbar'].scale.get()
            kwargs['cunits'] = self.gui.controls.axis_controllers['Colorbar'].units.value.get()
            kwargs['aspect'] = aspect
            kwargs['colorbar'] = self.colorbar

            self.colorbar.show()

        if self.drawn_object is None: kwargs['initialize'] = True
        
        self.drawn_object = method(*args,**kwargs)

        if globals.use_multiprocessing_on_scatter_plots:
            if self.drawn_object.thread is None:
                raise RuntimeError("Failed to spawn thread to draw the plot")

    def after_calculate(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.after_calculate")

        if self.track_and_annotate: self.annotate_tracked_particle()
        
        # Put the filename in the axis title for now
        #f = self.gui.filecontrols.current_file.get()
        #if len(f) > 30:
        #    f = "..."+f[-27:]
        #self.ax.set_title(f)

        # Make absolutely sure that the only drawn object on the axis is
        # the one we just created
        for child in self.ax.get_children():
            if isinstance(child,CustomAxesImage) and child is not self.drawn_object:
                child.remove()

        #if self.drawn_object not in self.canvas.blit_artists:
        #    self.canvas.blit_artists.append(self.drawn_object)
          
        self.canvas.draw_idle()
        
        self.previous_xlim = self.ax.get_xlim()
        self.previous_ylim = self.ax.get_ylim()

        self.gui.event_generate("<<PlotUpdate>>")

    def after_scatter_calculate(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.after_scatter_calculate")
        if not self.gui.data.is_image:
            self.previous_args = args
            self.previous_kwargs = kwargs

            # Only adjust the limits if any data was plotted
            xadaptive = self.gui.controls.axis_controllers['XAxis'].limits.adaptive.get()
            yadaptive = self.gui.controls.axis_controllers['YAxis'].limits.adaptive.get()
            cadaptive = self.gui.controls.axis_controllers['Colorbar'].limits.adaptive.get()

            controls_xlimits = [
                self.gui.controls.axis_controllers['XAxis'].limits.low.get(),
                self.gui.controls.axis_controllers['XAxis'].limits.high.get(),
            ]
            controls_ylimits = [
                self.gui.controls.axis_controllers['YAxis'].limits.low.get(),
                self.gui.controls.axis_controllers['YAxis'].limits.high.get(),
            ]
            controls_climits = [
                self.gui.controls.axis_controllers['Colorbar'].limits.low.get(),
                self.gui.controls.axis_controllers['Colorbar'].limits.high.get(),
            ]

            if ((xadaptive or np.nan in controls_xlimits) and
                (yadaptive or np.nan in controls_ylimits)): self.reset_xylim(which='both',draw=False)
            elif xadaptive or np.nan in controls_xlimits: self.reset_xylim(which='xlim',draw=False)
            elif yadaptive or np.nan in controls_ylimits: self.reset_xylim(which='ylim',draw=False)
        self.after_calculate(*args, **kwargs)
        
    def set_time_text(self,event=None):
        if globals.debug > 1: print("interactiveplot.set_time_text")
        try:
            text = "t = %f" % self.time.get()
        except tk.TclError as e:
            # If the user has read in time-series data in their files, then
            # just ignore setting the time text
            if "expected floating-point number but got" in str(e):
                return

        if self.time_text is not None:
            self.time_text.set_text(text)

        if event is not None:
            # Check if the mouse is inside the plot region
            widget = self.canvas.get_tk_widget()
            width = widget.winfo_width()
            height = widget.winfo_height()
        
            xpos = event.x_root - widget.winfo_rootx()
            ypos = height - (event.y_root - widget.winfo_rooty())
            if not ((0 <= xpos and xpos <= width) and
                    (0 <= ypos and ypos <= height)):
                return
            
            if self.time_text is None:
                self.time_text = self.ax.annotate(
                    text,
                    (xpos,ypos),
                    xycoords='figure pixels',
                )
            else:
                pos = self.time_text.get_position()
                if xpos == pos[0] and ypos == pos[1] and self.time_text.get_visible():
                    self.time_text.set_visible(False)
                else:
                    self.time_text.set_position((xpos,ypos))
                    self.time_text.set_visible(True)
        self.canvas.draw_idle()

    #def reset_clim(self, draw=True):
    #    if globals.debug > 1: print("interactiveplot.reset_clim")
    #    #self.canvas.draw() # I don't understand why we need to do this, but it works when we do...
    #    newlim = np.array(self.colorbar.calculate_limits(data=self.drawn_object._data))
    #    self.colorbar.set_clim(newlim)
    #    self.gui.controls.axis_controllers['Colorbar'].limits.on_axis_limits_changed()
    #    if draw: self.canvas.draw_idle()

    def reset_xylim(self,which='both',draw=True):
        if globals.debug > 1: print("interactiveplot.reset_xylim")
        
        new_xlim, new_ylim = self.calculate_xylim(which=which)

        xlim = np.array(self.ax.get_xlim())
        ylim = np.array(self.ax.get_ylim())
        
        if None not in new_xlim:
            if any(np.abs((new_xlim-xlim[xlim != 0])/xlim[xlim != 0]) > 0.001):
                self.ax.set_xlim(new_xlim)
                self.gui.controls.axis_controllers['XAxis'].limits.on_axis_limits_changed()
        if None not in new_ylim:
            if any(np.abs((new_ylim-ylim[ylim != 0])/ylim[ylim != 0]) > 0.001):
                self.ax.set_ylim(new_ylim)
                self.gui.controls.axis_controllers['YAxis'].limits.on_axis_limits_changed()
            
        if draw: self.canvas.draw_idle()
    
    def calculate_xylim(self, which='both', using=(None,None)):
        if globals.debug > 1: print("interactiveplot.calculate_xylim")

        if which not in ['xlim', 'ylim', 'both']:
            raise ValueError("Keyword 'which' must be one of 'xlim', 'ylim', or 'both'. Received ",which)

        new_xlim = [None, None]
        new_ylim = [None, None]

        xdata = None
        ydata = None
        if using[0] is not None: xdata = using[0]
        elif hasattr(self.gui, "data") and self.gui.data:
            xdata = self.gui.controls.axis_controllers['XAxis'].data
        if using[1] is not None: ydata = using[1]
        elif hasattr(self.gui, "data") and self.gui.data:
            ydata = self.gui.controls.axis_controllers['YAxis'].data

        if xdata is None and ydata is None:
            # Get the home view and use its limits as the new limits
            xmin, xmax, ymin, ymax = self.gui.plottoolbar.get_home_xylimits()
            new_xlim = np.array([xmin, xmax])
            new_ylim = np.array([ymin, ymax])
        else:
            if xdata is not None:
                xdata = xdata - self.origin[0]
                idx = np.isfinite(xdata)
                if np.any(idx):
                    xdata = xdata[idx]
                    new_xlim = np.array([np.nanmin(xdata), np.nanmax(xdata)])
            if ydata is not None:
                ydata = ydata - self.origin[1]
                idx = np.isfinite(ydata)
                if np.any(idx):
                    ydata = ydata[idx]
                    new_ylim = np.array([np.nanmin(ydata), np.nanmax(ydata)])

        xmargin, ymargin = self.ax.margins()
        if None not in new_xlim:
            # When dy or dx are zero, Matplotlib uses -margin, +margin limits
            dx = new_xlim[1]-new_xlim[0]
            if dx == 0: dx = 1.
            new_xlim = np.array([new_xlim[0]-dx*xmargin,new_xlim[1]+dx*xmargin])

        if None not in new_ylim:
            dy = new_ylim[1]-new_ylim[0]
            if dy == 0: dy = 1.
            new_ylim = np.array([new_ylim[0]-dy*ymargin,new_ylim[1]+dy*ymargin])
            
        if which == 'xlim': return new_xlim, [None, None]
        elif which == 'ylim': return [None, None], new_ylim
        else: return new_xlim, new_ylim
        
    # Intended to be used with canvas.mpl_connect('scroll_event', zoom)
    # https://stackoverflow.com/a/12793033/4954083
    def zoom(self, event, which="both"):
        if globals.debug > 1: print("interactiveplot.zoom")
        #print(event_in_axis(self.ax, event))
        if not event_in_axis(self.ax, event): return
        
        event = tkevent_to_matplotlibmouseevent(self.ax, event)
        
        # Cancel any queued zoom
        self.gui.plottoolbar.cancel_queued_zoom()

        # Seems that sometimes this method can be called incorrectly, so we prevent that here
        if event.xdata is None or event.ydata is None: return
        
        # Make the limits not be adaptive
        for axis_controller in self.gui.controls.axis_controllers.values():
            axis_controller.limits.adaptive_off()
        
        factor = 0.9
        if event.button == 'down': factor = 1./factor

        curr_xlim = self.gui.controls.axis_controllers['XAxis'].limits.get()
        curr_ylim = self.gui.controls.axis_controllers['YAxis'].limits.get()

        if self.track_id is None:
            x,y = self.mouse
            if None in [x,y]: return
        else:
            x = self.gui.controls.axis_controllers['XAxis'].data[self.track_id]
            y = self.gui.controls.axis_controllers['YAxis'].data[self.track_id]

        new_width = (curr_xlim[1]-curr_xlim[0])*factor
        new_height= (curr_ylim[1]-curr_ylim[0])*factor

        relx = (curr_xlim[1]-x)/(curr_xlim[1]-curr_xlim[0])
        rely = (curr_ylim[1]-y)/(curr_ylim[1]-curr_ylim[0])

        xlim = (
            x-new_width*(1-relx),
            x+new_width*(relx),
        )
        ylim = (
            y-new_height*(1-rely),
            y+new_height*(rely),
        )

        if which in ['both','x']:
            self.ax.set_xlim(xlim)
            self.gui.controls.axis_controllers['XAxis'].limits.set_limits(xlim)
        if which in ['both','y']:
            self.ax.set_ylim(ylim)
            self.gui.controls.axis_controllers['YAxis'].limits.set_limits(ylim)

        self.canvas.draw_idle()
        self.update()

    def start_pan(self, event):
        if globals.debug > 1: print("interactiveplot.start_pan")
        if not event_in_axis(self.ax, event): return
        
        # Disconnect the scroll wheel zoom binding while panning
        if self.hotkeys.is_bound("zoom"): self.hotkeys.unbind("zoom")
        if self.hotkeys.is_bound("zoom x"): self.hotkeys.unbind("zoom x")
        if self.hotkeys.is_bound("zoom y"): self.hotkeys.unbind("zoom y")
        
        # Trick Matplotlib into thinking we pressed the left mouse button
        event.button = 1
        # Strange that the y position gets mucked up, but this works
        event.y = self.canvas.get_tk_widget().winfo_height() - event.y
        self.gui.plottoolbar.press_pan(event)

    def drag_pan(self, event):
        if globals.debug > 1: print("interactiveplot.drag_pan")
        if not event_in_axis(self.ax, event): return
        event.key = 1
        event.y = self.canvas.get_tk_widget().winfo_height() - event.y
        # Check to make sure the mouse is inside an axis
        self.gui.plottoolbar.drag_pan(event)
        self.gui.controls.axis_controllers['XAxis'].limits.set_limits(self.ax.get_xlim())
        self.gui.controls.axis_controllers['YAxis'].limits.set_limits(self.ax.get_ylim())
        self.update()
        
    def stop_pan(self, event):
        if globals.debug > 1: print("interactiveplot.stop_pan")
        self.gui.plottoolbar.release_pan(event)
        # Reconnect the scroll wheel zoom binding
        if not self.hotkeys.is_bound("zoom"): self.hotkeys.bind("zoom", self.zoom)
        if not self.hotkeys.is_bound("zoom x"): self.hotkeys.bind("zoom x", lambda event: self.zoom(event, which='x'))
        if not self.hotkeys.is_bound("zoom y"): self.hotkeys.bind("zoom y", lambda event: self.zoom(event, which='y'))

    def color_particles(self, event):
        if globals.debug > 1: print("interactiveplot.color_particles")
        if not event_in_axis(self.ax, event): return

        if self.colorbar.visible:
            self.gui.message("Cannot change particle colors while using a colorbar")
            return

        # Only do this if we are in a scatter plot
        if isinstance(self.drawn_object, ScatterPlot):
            # We need to have a selection set before continuing
            if self.selection is None:
                self.gui.message("Click and drag on the plot to select particles, then try again",duration=5000)
                return

            x = self.gui.controls.axis_controllers['XAxis'].data
            y = self.gui.controls.axis_controllers['YAxis'].data

            xlim = self.selection[:2]
            ylim = self.selection[2:]

            IDs = np.logical_and(
                np.logical_and(xlim[0] <= x, x <= xlim[1]),
                np.logical_and(ylim[0] <= y, y <= ylim[1]),
            )
            
            self.colors[IDs] = int(event.keysym)
            
            self._update()

    # This method sets the origin to be at the particle closest to the mouse
    # position
    def track_particle(self, event=None, index=None):
        if globals.debug > 1: print("interactiveplot.track_particle")

        if globals.time_mode:
            self.gui.message("Cannot track particles while in time mode")
            return
        
        # We should always clear the old tracking no matter what
        self.clear_tracking()
        
        # Only do this if we are in a scatter plot
        if isinstance(self.drawn_object, ScatterPlot):
            data = np.column_stack((self.drawn_object.x,self.drawn_object.y))
            
            # Only get the mouse coordinates if this method was called by pressing the hotkey
            # Find the particle closest to the mouse position
            if None in self.mouse: return
            if event is not None:
                # If we don't do this transformation then if one axis has much larger numbers than
                # the other, the result is incorrect.
                screen_mouse = self.ax.transData.transform(self.mouse)
                screen_data = self.ax.transData.transform(data)
                self.track_id = self.get_closest_particle(screen_data, screen_mouse[0], screen_mouse[1])
            else:
                if index is None:
                    raise ValueError("Method track_particle must be called with keyword 'index' != None when keyword 'event' is not specified or is None")
                self.track_id = index

            if self.track_id is not None:
                # We are not allowed to have adaptive limits while tracking
                xlimits = self.gui.controls.axis_controllers['XAxis'].limits
                ylimits = self.gui.controls.axis_controllers['YAxis'].limits
                xlimits.adaptive_off()
                ylimits.adaptive_off()
                xlimits.adaptive_button.state(['disabled'])
                ylimits.adaptive_button.state(['disabled'])
                
                
                # Update the origin
                self.origin = data[self.track_id]
            
                self.gui.message("Started tracking particle "+str(self.track_id),duration=5000)
            
                self.canvas.draw_idle()
                self.update()

    def clear_tracking(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.clear_tracking")
        if self.track_id is not None:
            self.gui.message("Stopped tracking particle "+str(self.track_id),duration=5000)
        self.track_id = None
        self.clear_particle_annotation()
        self.track_and_annotate = False

        # Re-allow adaptive limits
        xlimits = self.gui.controls.axis_controllers['XAxis'].limits
        ylimits = self.gui.controls.axis_controllers['YAxis'].limits
        xlimits.adaptive_button.state(['!disabled'])
        ylimits.adaptive_button.state(['!disabled'])

    def annotate_tracked_particle(self, event=None):
        if globals.debug > 1: print("interactiveplot.annotate_tracked_particle")

        if globals.time_mode:
            self.gui.message("Cannot track particles in time mode")
            return
        
        if self.track_id is None: return
        if isinstance(self.drawn_object, ScatterPlot):
            if event is not None: self.track_and_annotate = True
            x = self.drawn_object.x[self.track_id]
            y = self.drawn_object.y[self.track_id]
            self.particle_annotation.set_text(str(self.track_id))
            #self.particle_annotation.set_transform(self.ax.transData)
            self.particle_annotation.set_position((x,y))

    def clear_particle_annotation(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.clear_particle_annotation")
        self.particle_annotation.set_text("")
        self.canvas.draw_idle()

    def get_closest_particle(self, data, x, y):
        if globals.debug > 1: print("interactiveplot.get_closest_particle")
        return find_nearest_2d(data,np.array([x,y]))

    # event needs to be a Matplotlib event from mpl_connect
    def press_select(self, event):
        # Callback for mouse button press to select particles
        if self.gui.plottoolbar.mode != "": return
        if event.button == 1 and None not in [event.x,event.y]:
            self.gui.plottoolbar.cancel_queued_zoom()
            self.selection = None
            id_select = self.canvas.mpl_connect("motion_notify_event", self.drag_select)
            self._select_info = collections.namedtuple("_SelectInfo", "start_xy start_xy_data cid")(
                start_xy=(event.x, event.y), start_xy_data=(event.xdata,event.ydata), cid=id_select)

    def drag_select(self, event):
        start_xy = self._select_info.start_xy
        (x1, y1), (x2, y2) = np.clip(
            [start_xy, [event.x, event.y]], self.ax.bbox.min, self.ax.bbox.max)
        if abs(x2-x1) >= globals.minimum_selection_size and abs(y2-y1) >= globals.minimum_selection_size:
            self.selection = np.array([x1,x2,y1,y2])
            self.gui.plottoolbar.draw_rubberband(event, x1, y1, x2, y2)

    def release_select(self, event):
        if self._select_info is None: return
        self.canvas.mpl_disconnect(self._select_info.cid)
        if self.selection is not None and not self.colorbar.visible:
            transformed = self.ax.transData.inverted().transform([[self.selection[0],self.selection[2]],[self.selection[1],self.selection[3]]])
            self.selection[0] = min(transformed[0][0],transformed[1][0])
            self.selection[1] = max(transformed[0][0],transformed[1][0])
            self.selection[2] = min(transformed[0][1],transformed[1][1])
            self.selection[3] = max(transformed[0][1],transformed[1][1])
            self.gui.message("Press 0-9 to change selected particles' colors")
        self._select_info = None

    # style is a list or tuple
    def set_style(self,style):
        if globals.debug > 1: print("interactiveplot.set_style")

        if not isinstance(style, (list,tuple)):
            raise TypeError("'style' must be either a list or a tuple, not '"+type(style).__name__+".")
        
        rcParams = {}
        for s in style:
            # Construct rcParams from the default file
            if s == 'default': d = matplotlib.rc_params()
            # Get rcParams from the style library
            else: d = matplotlib.style.library[s]
            for key in d:
                if key not in rcParams.keys():
                    rcParams[key] = d[key]

        self.update_rcParams(rcParams)
        
    # Matplotlib refuses to change its style after it has already drawn stuff.
    # So here we instead force changes to the artists to simulate as if everything
    # was redrawn
    def update_rcParams(self,new_rcParams):
        if globals.debug > 1: print("interactiveplot.update_rcParams")
        # Completely update the figure by clearing everything and redrawing.
        # Most things in rcParams are supported, but some are not

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
        
            for key,val in new_rcParams.items():
                matplotlib.pyplot.rcParams[key] = val

            ax = self.ax
            figure = ax.get_figure()

            # Store keywords
            figkw = {key:val for key,val in new_rcParams.items() if 'figure.' in key}
            fontkw = {key:val for key,val in new_rcParams.items() if 'font.' in key}
            lineskw = {key:val for key,val in new_rcParams.items() if 'lines.' in key}
            axeskw = {key:val for key,val in new_rcParams.items() if 'axes.' in key}
            textkw = {key:val for key,val in new_rcParams.items() if 'text.' in key}
            xtickkw = {key:val for key,val in new_rcParams.items() if 'xtick.' in key}
            ytickkw = {key:val for key,val in new_rcParams.items() if 'ytick.' in key}

            # Update the figure parameters
            keys = figkw.keys()
            if 'figure.subplot' in keys:
                word = 'figure.subplot'
                kws = ['bottom','hspace','left','right','top','wspace']
                words = [word+'.'+w for w in kws]
                kw = {}
                for key in words:
                    kw[key] = figkw.get(key,None)
                figure.subplots_adjust(**kw)
            # Do our best to capture keywords by the 'set' commands in an effort
            # to make our code future compatible as best as we can
            figdir = dir(figure)
            for key,val in figkw.items():
                keycheck = key.replace('figure.','')
                for d in [f for f in figdir if 'set_' in f and keycheck in f]:
                    if "dpi" not in d:
                        getattr(figure,d)(val)

            # Tick parameters
            xtick_minor_visible = new_rcParams.get('xtick.minor.visible',False)
            ytick_minor_visible = new_rcParams.get('ytick.minor.visible',False)

            # Font properties
            keys = inspect.getargspec(matplotlib.font_manager.FontProperties.__init__).args
            kwargs = {}
            for key in keys:
                for k,v in fontkw.items():
                    if key in k:
                        kwargs[key] = v
            font = matplotlib.font_manager.FontProperties(**kwargs)

            # Update the axis
            if xtick_minor_visible and ytick_minor_visible:
                ax.minorticks_on()
            else:
                ax.minorticks_on()
                xlocator = ax.xaxis.get_minor_locator()
                ylocator = ax.yaxis.get_minor_locator()
                ax.minorticks_off()

                if xtick_minor_visible:
                    ax.xaxis.set_minor_locator(xlocator)
                if ytick_minor_visible:
                    ax.yaxis.set_minor_locator(ylocator)


            # Update the ticks
            for axis,tickkw in zip(['x','y'],[xtickkw,ytickkw]):
                minorvisible = tickkw.pop(axis+"tick.minor.visible", None)
                if minorvisible is not None:
                    if axis == 'x':
                        ax.tick_params(axis=axis,which='minor',bottom=minorvisible,top=minorvisible)
                    else:
                        ax.tick_params(axis=axis,which='minor',left=minorvisible,right=minorvisible)

                major_stuff = {}
                minor_stuff = {}
                for key, val in tickkw.items():
                    if 'major' in key:
                        real_key = key.split(".")[-1]
                        major_stuff[real_key] = val
                    elif 'minor' in key:
                        real_key = key.split(".")[-1]
                        minor_stuff[real_key] = val
                for key,val in major_stuff.items():
                    try:
                        ax.tick_params(axis=axis,which='major',**{key:val})
                    except ValueError: pass

                for key,val in minor_stuff.items():
                    try:
                        ax.tick_params(axis=axis,which='minor',**{key:val})
                    except ValueError: pass
                        
                stuff = {}
                for key, val in tickkw.items():
                    if 'major' not in key and 'minor' not in key:
                        real_key = key.split(".")[-1]
                        stuff[real_key] = val

                for key,val in stuff.items():
                    try:
                        ax.tick_params(axis=axis,which='both',**{key:val})
                    except ValueError: pass

            # Update fonts and objects that have text
            spines = [val for key,val in ax.spines.items()]
            patch = ax.patch
            xticklines = ax.get_xticklines()
            yticklines = ax.get_yticklines()
            dirax = dir(ax)
            for key,val in axeskw.items():
                attr = key.replace('axes.','')
                if 'set_'+attr in dirax:
                    getattr(ax,'set_'+attr)(val)
                else:
                    if attr == 'edgecolor': # This means to color the spines
                        for side,spine in ax.spines.items(): 
                            spine.set_color(val)

            for child in self.get_all_ax_children():
                # Make global edits to text
                if hasattr(child, "set_fontproperties"):
                    child.set_fontproperties(font)
                if 'text.color' in textkw:
                    if isinstance(child, matplotlib.text.Text):
                        child.set_color(textkw['text.color'])
                
        # Draw the new figure
        self.canvas.draw()


    def get_all_ax_children(self,obj=None,result=[]):
        if globals.debug > 1: print("interactiveplot.get_all_ax_children")

        if obj is None: obj = self.ax
        if obj is not self.ax and obj not in result: result.append(obj)
        if hasattr(obj,"get_children"):
            for child in obj.get_children():
                if child not in result: result.append(child)
                self.get_all_ax_children(obj=child,result=result)
        else:
            if child not in result: result.append(obj)
        return result
