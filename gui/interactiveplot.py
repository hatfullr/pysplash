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
from lib.surfacevalueplot import SurfaceValuePlot
from lib.tkvariable import StringVar, IntVar, DoubleVar, BooleanVar
from lib.plotannotations import PlotAnnotations

from functions.findnearest2d import find_nearest_2d
from functions.stringtofloat import string_to_float
from functions.eventinaxis import event_in_axis
from functions.tkeventtomatplotlibmouseevent import tkevent_to_matplotlibmouseevent
from functions.getallchildren import get_all_children
from functions.hotkeystostring import hotkeys_to_string
from functions.annotateparticle import AnnotateParticle
from functions.setwidgetstatepermanent import set_widget_state_permanent, release_widget_state_permanent
from functions.setpreference import set_preference
from functions.getpreference import get_preference

from widgets.resizableframe import ResizableFrame
from widgets.loadingwheel import LoadingWheel

import warnings
import inspect
import traceback
import ast

class InteractivePlot(ResizableFrame,object):
    default_cursor_inside_axes = matplotlib.backend_tools.Cursors.SELECT_REGION
    default_cursor_outside_axes = matplotlib.backend_tools.Cursors.POINTER
    # This needs to be a list or tuple
    plot_types_allowed_tracking = (ScatterPlot, SurfaceValuePlot)
    
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

        self.tracking = self.track_id.get() >= 0
        
        self.previous_args = None
        self.previous_kwargs = None
        self.previous_xlim = None
        self.previous_ylim = None
        self.previous_time_mode = globals.time_mode

        self._origin = np.zeros(2)
        self.origin_cid = None
        self._colors = None

        self._select_info = None

        self.selection = None

        self.plot_annotations = PlotAnnotations(self.ax)

        self.making_movie = False

        # Create an annotation which asks the user to import data if there isn't any
        self.import_data_annotation = self.fig.text(
            0.5,0.5,
            "No available data\nGo to Data > Import "+hotkeys_to_string("import data")+" to import data",
            va='center',ha='center',
            transform=self.fig.transFigure,
        )

        self.choose_data_annotation = self.fig.text(
            0.5,0.5,
            "Choose data to plot\nusing the controls on the right",
            va='center',ha='center',
            transform=self.fig.transFigure,
        )

        # If the user clicks anywhere on the plot, focus the plot.
        for child in self.winfo_children():
            child.bind("<Button-1>", lambda *args, **kwargs: self.canvas.get_tk_widget().focus_set(), add="+")
        
        self.canvas.mpl_connect('button_press_event', self.press_select)
        self.canvas.mpl_connect('button_release_event', self.release_select)
        
        self.mouse = np.array([None,None])
        self.canvas.mpl_connect("axes_leave_event", self.clear_mouse)
        self.canvas.mpl_connect("motion_notify_event", self.update_mouse)

        # This keeps the "x=...,y=..." text updated whenever the canvas gets redrawn
        self.canvas_motion_event = None
        def on_motion(event):
            self.canvas_motion_event = event
        self.canvas.get_tk_widget().bind("<Motion>", on_motion, add="+")
        self.canvas.mpl_connect("draw_event", self._on_draw)
            
        self.bind = lambda *args, **kwargs: self.canvas.get_tk_widget().bind(*args,**kwargs)
        self.unbind = lambda *args, **kwargs: self.canvas.get_tk_widget().unbind(*args,**kwargs)

        self._after_id_update = None

        # Apply the style given in the user's preferences
        self._set_style()

        # Apply the user's preferences for subplot_adjust parameters
        self.subplots_adjust(
            left=self.left.get(),
            right=self.right.get(),
            top=self.top.get(),
            bottom=self.bottom.get(),
            hspace=self.hspace.get(),
            wspace=self.wspace.get(),
        )

        self._updating = False

    @property
    def colors(self): return self._colors
    @colors.setter
    def colors(self, value):
        self._colors = value
        set_preference(self, "colors", value if value is None else value.tolist())

    @property
    def origin(self): return self._origin
    @origin.setter
    def origin(self, value):
        # If the origin is trying to be set to a non-finite value then it
        # means that e.g. the user is looking at log10 data of some quantity
        # and that the tracked particle has a linear value of <= 0, such that
        # its log value is not finite. Thus, we need to clear the tracking.
        if np.any(~np.isfinite(value)):
            self.clear_tracking(reason="the particle has a non-finite value on the plot")
        else:
            self._origin = value
        
    def create_variables(self):
        if globals.debug > 1: print("interactiveplot.create_variables")
        self.xycoords = tk.StringVar()
        self.time = DoubleVar(self,None,'time')
        self.style = StringVar(self,["default"],'style')
        self.track_id = IntVar(self, -1, 'track')
        
        self.time.trace('w',lambda *args, **kwargs: self.set_time_text())
        self.style.trace('w', self._set_style)

        # These are for adjusting plot spacing etc.
        self.top = DoubleVar(self,self.fig.subplotpars.top,'top')
        self.bottom = DoubleVar(self,self.fig.subplotpars.bottom,'bottom')
        self.left = DoubleVar(self,self.fig.subplotpars.left,'left')
        self.right = DoubleVar(self,self.fig.subplotpars.right,'right')
        self.hspace = DoubleVar(self,self.fig.subplotpars.hspace,'hspace')
        self.wspace = DoubleVar(self,self.fig.subplotpars.wspace,'wspace')

    def create_widgets(self):
        if globals.debug > 1: print("interactiveplot.create_widgets")
        #self.canvas = CustomCanvas(self.fig, master=self)
        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.xycoords_label = tk.Label(self,textvariable=self.xycoords,bg='white')
        self.loading_wheel = LoadingWheel(self, 'sw', bg='white')

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
        self.hotkeys.bind("track and annotate particle", self.track_and_annotate)#(
        #lambda event: self.track_particle(event),
        #    lambda event: self.annotate_tracked_particle(event),
        #))
        self.hotkeys.bind("annotate time", lambda event: self.set_time_text(event))
        self.hotkeys.bind("annotate particle", lambda *args,**kwargs: self.annotate_particle())
        for i in range(10):
            self.hotkeys.bind("particle color "+str(i), self.color_particles)
            
    def destroy(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.destroy")
        
        if hasattr(self, "_after_id_update") and self._after_id_update is not None:
            self.after_cancel(self._after_id_update)
            self._after_id_update = None
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
        self.canvas.draw_idle()

    def reset_colors(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.reset_colors")
        self.colors = None

    def clear_particle_annotations(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.clear_particle_annotations")
        for key in self.plot_annotations.keys():
            try: int(key)
            except: pass
            self.plot_annotations.remove(key)

    # Draw the figure
    def draw(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.draw")
        #self.loading_wheel.show()
        self.canvas.draw_idle()
        self.canvas.flush_events()
        #self.loading_wheel.hide()
        
    def update(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update")
        # If we are waiting to update, then make sure the controls' update button is disabled
        #self.gui.controls.update_button.state(['disabled'])
        self.loading_wheel.show()
        #if self._updating: return
        
        if globals.plot_update_delay > 0:
            if self._after_id_update is not None:
                self.after_cancel(self._after_id_update)
            self._after_id_update = self.after(globals.plot_update_delay, self._update)
        else: self._update()
    
    def _update(self,*args, **kwargs):
        if globals.debug > 1:
            print("interactiveplot._update")
            print("    self.ax = ",self.ax)

        self._updating = True
        self.loading_wheel.show()
            
        if self._after_id_update is not None:
            self.after_cancel(self._after_id_update)
            self._after_id_update = None

        # Stale the axis controllers before fetching their data, so that we
        # obtain fresh data
        for axis_controller in self.gui.controls.axis_controllers.values():
            axis_controller.stale = True

        xaxis = self.gui.controls.axis_controllers['XAxis']
        yaxis = self.gui.controls.axis_controllers['YAxis']
        x, x_display_units, x_physical_units = xaxis.data, xaxis.display_units, xaxis.physical_units
        y, y_display_units, y_physical_units = yaxis.data, yaxis.display_units, yaxis.physical_units

        # Don't try to plot anything if there's no data to plot
        if x is None or y is None:
            # Update the 'help' text in the plot
            self.update_help_text()
            self.draw()
            return

        self.origin = np.zeros(2)
        if self.tracking and self.track_id.get() in np.arange(len(x)):
            self.origin = np.array([x[self.track_id.get()],y[self.track_id.get()]])

        if (xaxis.value.get() in ['x','y','z'] and
            yaxis.value.get() in ['x','y','z']):
            aspect = 'equal'
        else:
            aspect = None

        # If there's no data to plot, stop here
        if not self.gui.data:
            self.after_calculate()
            return

        self.gui.event_generate("<<BeforePlotUpdate>>")
        
        kwargs = {
            'aftercalculate' : self.after_calculate, # Overwritten for some plot types
            'aspect' : aspect,
        }
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
            else:
                method = ScatterPlot
                args = (
                    self.ax,
                    x,
                    y,
                )

                if self.colors is None:
                    self.colors = np.full(len(x), ScatterPlot.default_color_index)
                
                kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
                kwargs['c'] = self.colors
                kwargs['aftercalculate'] = self.after_scatter_calculate
                
                self.colorbar.hide()

        elif colorbar_text.strip() == 'Point Density':
            method = PointDensityPlot
            args = (
                self.ax,
                x,
                y,
            )
            
            kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
            kwargs['aftercalculate'] = self.after_scatter_calculate
            kwargs['colorbar'] = self.colorbar
                
        elif self.gui.controls.colorbar_integrated_surface.get() == 'integrated':
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

            kwargs['colorbar'] = self.colorbar
            
        elif self.gui.controls.colorbar_integrated_surface.get() == 'surface':
            caxis = self.gui.controls.axis_controllers['Colorbar']
            A, A_display_units, A_physical_units = caxis.data, caxis.display_units, caxis.physical_units
            if A is None or A_display_units is None or A_physical_units is None:
                raise Exception("One of A, A_display_units, or A_physical_units was None. This should never happen.")
            
            h = self.gui.get_display_data('h')
            
            # We need z information (direction into the screen)
            xvalue = self.gui.controls.axis_controllers['XAxis'].value.get()
            yvalue = self.gui.controls.axis_controllers['YAxis'].value.get()
            vals = (xvalue,yvalue)
            if   vals in [('x','y'), ('y','x')]: z = self.gui.get_data('z')
            elif vals in [('x','z'), ('z','x')]: z = self.gui.get_data('y')
            elif vals in [('y','z'), ('z','y')]: z = self.gui.get_data('x')
            else:
                raise Exception("expected the xaxis and yaxis to each be one of 'x', 'y', or 'z', but found xaxis='"+xvalue+"' and yaxis='"+yvalue+"' instead")
            
            method = SurfaceValuePlot
            args = (
                self.ax,
                A,
                x,
                y,
                z,
                h,
                [ # physical units
                    A_physical_units,
                    x_physical_units,
                    y_physical_units,
                    self.gui.get_physical_units('h'),
                ],
                [ # display units
                    A_display_units,
                    x_display_units,
                    y_display_units,
                    self.gui.get_display_units('h'),
                ],
            )

            kwargs['colorbar'] = self.colorbar

        if self.tracking and method in InteractivePlot.plot_types_allowed_tracking:
            xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
            dx = 0.5*(xlim[1]-xlim[0])
            dy = 0.5*(ylim[1]-ylim[0])
            xlim = (self.origin[0]-dx,self.origin[0]+dx)
            ylim = (self.origin[1]-dy,self.origin[1]+dy)
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
            xaxis.limits.set_limits(xlim)
            yaxis.limits.set_limits(ylim)

        if self.drawn_object is None: kwargs['initialize'] = True
        else:
            self.drawn_object.cancel()
            self.drawn_object = None

        # Make sure there is only 1 drawn object at any given time
        for child in self.ax.get_children():
            if isinstance(child,CustomAxesImage):
                child.remove()

        if self.making_movie:
            kwargs["resolution_steps"] = tuple([1])

        if method is not ScatterPlot: self.disable()
        self.gui.message("Drawing plot",duration=None)
        self._first_after_calculate = True

        
        self.drawn_object = method(*args,**kwargs)

        if globals.use_multiprocessing:
            if self.drawn_object.thread is None:
                raise RuntimeError("Failed to spawn thread to draw the plot")

    def after_calculate(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.after_calculate")

        if self._first_after_calculate:
            xydata = self.get_xy_data()
            renderer = self.canvas.get_renderer()
            for ID, annotation in self.plot_annotations.items():
                try: int(ID)
                except: continue
                self.plot_annotations.configure(ID, position=xydata[int(ID)])
        
        self._first_after_calculate = False

        if self.drawn_object is not None and self.drawn_object.calculating:
            if not isinstance(self.drawn_object, ScatterPlot): self.colorbar.show()
            else: self.colorbar.hide()
            
            self.draw()
        else:
            # Make absolutely sure that the only drawn object on the axis is
            # the one we just created
            for child in self.ax.get_children():
                if isinstance(child,CustomAxesImage) and child is not self.drawn_object:
                    child.remove()

            #if self.drawn_object not in self.canvas.blit_artists:
            #    self.canvas.blit_artists.append(self.drawn_object)

            self.update_help_text()

            self.gui.event_generate("<<PlotUpdate>>")

            self.draw()

            self.previous_xlim = self.ax.get_xlim()
            self.previous_ylim = self.ax.get_ylim()
            self.loading_wheel.hide()
            self._updating = False
            self.gui.message.clear(check="Drawing plot")
            self.enable()

    def after_scatter_calculate(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.after_scatter_calculate")
        if not self.gui.data.is_image and not self.tracking:
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

        if 'time' in self.plot_annotations.keys():
            self.plot_annotations.configure('time',text=text)
            #self.time_text.set_text(text)

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
            
            if 'time' not in self.plot_annotations.keys():
                self.plot_annotations.add("time", text, (xpos,ypos), xycoords='figure pixels')
                #self.time_text = self.ax.annotate(
                #    text,
                #    (xpos,ypos),
                #    xycoords='figure pixels',
                #)
            else:
                pos = self.plot_annotations['time'].get_position()
                #pos = self.time_text.get_position()
                if xpos == pos[0] and ypos == pos[1] and self.time_text.get_visible():
                    self.plot_annotations.configure('time',visible=False)
                    #self.time_text.set_visible(False)
                else:
                    self.plot_annotations.configure('time',position=(xpos,ypos),visible=True)
                    #self.time_text.set_position((xpos,ypos))
                    #self.time_text.set_visible(True)
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
            
        if draw: self.draw()
    
    def calculate_xylim(self, which='both', using=(None,None)):
        if globals.debug > 1: print("interactiveplot.calculate_xylim")

        if which not in ['xlim', 'ylim', 'both']:
            raise ValueError("Keyword 'which' must be one of 'xlim', 'ylim', or 'both'. Received ",which)

        new_xlim = [None, None]
        new_ylim = [None, None]

        xaxis = self.gui.controls.axis_controllers['XAxis']
        yaxis = self.gui.controls.axis_controllers['YAxis']
        
        xdata = using[0] if using[0] is not None else xaxis.data
        ydata = using[1] if using[1] is not None else yaxis.data

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
        if not event_in_axis(self.ax, event): return
        
        event = tkevent_to_matplotlibmouseevent(self.ax, event)

        # Cancel any queued zoom
        self.gui.plottoolbar.cancel_queued_zoom()

        # Seems that sometimes this method can be called incorrectly, so we prevent that here
        if event.xdata is None or event.ydata is None: return
        
        # Make the limits not be adaptive
        if not self.tracking:
            for axis_controller in self.gui.controls.axis_controllers.values():
                if axis_controller.limits.adaptive.get():
                    axis_controller.limits.adaptive_button.invoke()
        
        factor = 0.9
        if event.button == 'down': factor = 1./factor

        curr_xlim = self.gui.controls.axis_controllers['XAxis'].limits.get()
        curr_ylim = self.gui.controls.axis_controllers['YAxis'].limits.get()

        if self.tracking:
            xy = self.get_xy_data()
            x = xy[:,0][self.track_id.get()]
            y = xy[:,1][self.track_id.get()]
        else:
            x,y = self.mouse
            if None in [x,y]: return

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

        self.draw()
        
        if isinstance(self.drawn_object, ScatterPlot):
            self.update()
        else:
            self.gui.controls.update_button.configure(state='!disabled')

    def start_pan(self, event):
        if globals.debug > 1: print("interactiveplot.start_pan")
        if not event_in_axis(self.ax, event): return

        if self.tracking:
            self.gui.message("Cannot pan while tracking a particle. Press "+hotkeys_to_string("track particle")+" outside the axis to disable.")
            return
        
        
        # Disconnect the scroll wheel zoom binding while panning
        self.hotkeys.disable('zoom')
        self.hotkeys.disable('zoom x')
        self.hotkeys.disable('zoom y')
        
        # Trick Matplotlib into thinking we pressed the left mouse button
        event.button = 1
        # Strange that the y position gets mucked up, but this works
        event.y = self.canvas.get_tk_widget().winfo_height() - event.y
        self.gui.plottoolbar.press_pan(event)

    def drag_pan(self, event):
        if globals.debug > 1: print("interactiveplot.drag_pan")
        if not event_in_axis(self.ax, event): return
        if self.tracking: return
        
        event.key = 1
        event.y = self.canvas.get_tk_widget().winfo_height() - event.y
        # Check to make sure the mouse is inside an axis
        self.gui.plottoolbar.drag_pan(event)
        self.gui.controls.axis_controllers['XAxis'].limits.set_limits(self.ax.get_xlim())
        self.gui.controls.axis_controllers['YAxis'].limits.set_limits(self.ax.get_ylim())
        if isinstance(self.drawn_object, ScatterPlot):
            self.update()
        else:
            self.gui.controls.update_button.configure(state='!disabled')
        
    def stop_pan(self, event):
        if globals.debug > 1: print("interactiveplot.stop_pan")
        if self.tracking: return
        
        self.gui.plottoolbar.release_pan(event)
        # Reconnect the scroll wheel zoom binding
        self.hotkeys.enable('zoom')
        self.hotkeys.enable('zoom x')
        self.hotkeys.enable('zoom y')

    def color_particles(self, event, particles=None, index=None, update=True):
        if globals.debug > 1: print("interactiveplot.color_particles")

        if event is not None and not event_in_axis(self.ax, event): return
        if event is None and (particles is None or index is None): return
        
        if self.colorbar.visible:
            self.gui.message("Cannot change particle colors while using a colorbar")
            return

        xy = self.get_xy_data()
        colors = self.colors if self.colors is not None else np.full(len(xy), ScatterPlot.default_color_index)

        # Only do this if we are in a scatter plot
        if isinstance(self.drawn_object, ScatterPlot):
            IDs = None
            
            if particles is None:
                # We need to have a selection set before continuing
                if self.selection is None:
                    self.gui.message("Click and drag on the plot to select particles, then try again")
                    return

                xlim = self.selection[:2]
                ylim = self.selection[2:]

                x = xy[:,0]
                y = xy[:,1]

                IDs = np.logical_and(
                    np.logical_and(xlim[0] <= x, x <= xlim[1]),
                    np.logical_and(ylim[0] <= y, y <= ylim[1]),
                )
            else:
                IDs = particles
            
            if IDs is not None:
                if event is not None:
                    colors[IDs] = int(event.keysym) if index is None else index
                else: colors[IDs] = index
                if update: self._update()
                    
        elif particles is not None and index is not None:
            colors[particles] = index
            if update: self._update()
        
        self.colors = colors

    # This method sets the origin to be at the particle closest to the mouse
    # position
    def track_particle(self, event=None, index=None):
        if globals.debug > 1: print("interactiveplot.track_particle")

        if globals.time_mode:
            self.gui.message("Cannot track particles while in time mode")
            return

        if index is None:
            if None in self.mouse: # Mouse is outside the axis
                self.clear_tracking()
                return
        
        # Only do this if we are in either a scatter plot or a surface value plot
        if isinstance(self.drawn_object, InteractivePlot.plot_types_allowed_tracking):
            self.tracking = event is not None or index is not None
            
            # Only get the mouse coordinates if this method was called by pressing the hotkey
            # Find the particle closest to the mouse position
            if event is not None:
                self.track_id.set(self.get_closest_particle_to_mouse())
            else:
                if index is None:
                    raise ValueError("Method track_particle must be called with keyword 'index' != None when keyword 'event' is not specified or is None")
                self.track_id.set(index)
            
            # We are not allowed to have adaptive limits while tracking
            xlimits = self.gui.controls.axis_controllers['XAxis'].limits
            ylimits = self.gui.controls.axis_controllers['YAxis'].limits
            xlimits.adaptive_off()
            ylimits.adaptive_off()
            set_widget_state_permanent(xlimits.adaptive_button,['disabled'])
            set_widget_state_permanent(ylimits.adaptive_button,['disabled'])
            
            # Update the origin
            self.origin = self.get_xy_data()[self.track_id.get()]
            
            self.gui.message("Started tracking particle "+str(self.track_id.get()))

            if isinstance(self.drawn_object, InteractivePlot.plot_types_allowed_tracking):
                self.update()
            else:
                self.gui.controls.update_button.configure(state='!disabled')

    def track_and_annotate(self, event):
        if globals.debug > 1: print("interactiveplot.track_and_annotate")
        if None in self.mouse: # Mouse is outside axis
            self.plot_annotations.remove(str(self.track_id.get()))
            self.clear_tracking()
        else:
            self.track_particle(event=event)
            self.annotate_tracked_particle(event=event)
                
    def clear_tracking(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.clear_tracking")
        if self.track_id.get() != -1:
            if self.tracking:
                message = "Stopped tracking particle "+str(self.track_id.get())
                reason = kwargs.get('reason',None)
                if reason is not None:
                    message += " because "+reason
                self.gui.message(message, persist=reason is not None)
        
            self.tracking = False
            self.track_id.set(-1)
            
            # Re-allow adaptive limits
            xlimits = self.gui.controls.axis_controllers['XAxis'].limits
            ylimits = self.gui.controls.axis_controllers['YAxis'].limits
            release_widget_state_permanent(xlimits.adaptive_button)
            release_widget_state_permanent(ylimits.adaptive_button)
            xlimits.adaptive_button.configure(state='!disabled')
            ylimits.adaptive_button.configure(state='!disabled')

    def annotate_tracked_particle(self, event=None):
        if globals.debug > 1: print("interactiveplot.annotate_tracked_particle")

        if globals.time_mode:
            self.gui.message("Cannot track particles in time mode")
            return
        
        if not self.tracking: return
        if isinstance(self.drawn_object, InteractivePlot.plot_types_allowed_tracking):
            self.annotate_particle(ID=self.track_id.get())

    def annotate_particle(self, ID=None, draw=True):
        if globals.debug > 1: print("interactiveplot.annotate_particle")
        
        if globals.time_mode:
            self.gui.message("Cannot annotate particles in time mode")
            return
        
        if isinstance(self.drawn_object, InteractivePlot.plot_types_allowed_tracking):
            ID_orig = ID
            if ID is None:
                ID = self.get_closest_particle_to_mouse()
                # Mouse is outside the axis
                if ID is None:
                    AnnotateParticle(self.gui)
                    return
            
            xy = self.get_xy_data()[ID]
            # Make a new annotation
            if str(ID) not in self.plot_annotations.keys():
                self.plot_annotations.add(str(ID),str(ID),xy,clip_on=True)
                if draw: self.draw()
                return self.plot_annotations[str(ID)]
            elif ID_orig is None: # User chose an already-annotated particle, so clear that annotation
                self.plot_annotations.remove(str(ID))
                if draw: self.draw()
        return None

    def get_closest_particle(self, data, x, y):
        if globals.debug > 1: print("interactiveplot.get_closest_particle")
        return int(find_nearest_2d(data,np.array([x,y])))

    def get_closest_particle_to_mouse(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.get_closest_particle_to_mouse")

        # If the mouse is outside the axis
        if None in self.mouse: return None
        
        data = self.get_xy_data()
        screen_mouse = self.ax.transData.transform(self.mouse)
        screen_data = self.ax.transData.transform(data)
        ID = self.get_closest_particle(screen_data, screen_mouse[0], screen_mouse[1])
        return ID

    def get_xy_data(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.get_xy_data")
        if self.drawn_object is not None:
            return np.column_stack((self.drawn_object.x,self.drawn_object.y))
        else:
            return np.column_stack((
                self.gui.controls.axis_controllers['XAxis'].combobox.get()[0],
                self.gui.controls.axis_controllers['YAxis'].combobox.get()[0],
            ))

    # event needs to be a Matplotlib event from mpl_connect
    def press_select(self, event):
        if globals.debug > 1: print("interactiveplot.press_select")
        if (event.button == matplotlib.backend_bases.MouseButton.RIGHT):
            self.gui.plottoolbar.cancel_queued_zoom()
        elif (event.button == matplotlib.backend_bases.MouseButton.LEFT):
            # Callback for mouse button press to select particles
            if self.gui.plottoolbar.mode != "": return
            if event.button == 1 and None not in [event.x,event.y]:
                self.gui.plottoolbar.cancel_queued_zoom()
                self.selection = None
                id_select = self.canvas.mpl_connect("motion_notify_event", self.drag_select)
                self._select_info = collections.namedtuple("_SelectInfo", "start_xy start_xy_data cid")(
                    start_xy=(event.x, event.y), start_xy_data=(event.xdata,event.ydata), cid=id_select)

    def drag_select(self, event):
        if globals.debug > 1: print("interactiveplot.drag_select")
        start_xy = self._select_info.start_xy
        (x1, y1), (x2, y2) = np.clip(
            [start_xy, [event.x, event.y]], self.ax.bbox.min, self.ax.bbox.max)
        if abs(x2-x1) >= globals.minimum_selection_size and abs(y2-y1) >= globals.minimum_selection_size:
            self.selection = np.array([x1,x2,y1,y2])
            self.gui.plottoolbar.draw_rubberband(event, x1, y1, x2, y2)

    def release_select(self, event):
        if globals.debug > 1: print("interactiveplot.release_select")
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

    def _set_style(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot._set_style")
        self.set_style(self.style.get())
        
    # style is a list or tuple
    def set_style(self,style):
        if globals.debug > 1: print("interactiveplot.set_style")

        if not isinstance(style, (list,tuple)):
            try:
                style = list(ast.literal_eval(style))
            except:
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

    def subplots_adjust(self, **kwargs):
        # Only move the axis around, not the colorbar
        pos = self.ax.get_position()

        left = kwargs.get('left',pos.x0)
        right = kwargs.get('right',pos.x1)
        bottom = kwargs.get('bottom',pos.y0)
        top = kwargs.get('top',pos.y1)
        
        x0 = min(left,right)
        x1 = max(left,right)
        y0 = min(bottom,top)
        y1 = max(bottom,top)
        width = x1 - x0
        height = y1 - y0
        self.ax.set_position([x0,y0,width,height])

        self.canvas.draw_idle()

    def update_help_text(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot.update_help_text")
        
        if self.drawn_object is not None:
            self.import_data_annotation.set_visible(False)
            self.choose_data_annotation.set_visible(False)
        else:
            # If there is no data to show, display the annotation which asks the user to import data
            self.import_data_annotation.set_visible(len(self.gui.filenames) == 0)

            # If there is data to show, but the user hasn't chosen the data they want yet,
            # display the annotation which instructs them to pick data from the controls
            if hasattr(self.gui, 'controls'):
                self.choose_data_annotation.set_visible(len(self.gui.filenames) > 0 and
                                                        (self.gui.controls.axis_controllers['XAxis'].value.get() in [None,''] or
                                                         self.gui.controls.axis_controllers['YAxis'].value.get() in [None,'']))
            else: self.choose_data_annotation.set_visible(False)

    def _on_draw(self, *args, **kwargs):
        if globals.debug > 1: print("interactiveplot._on_draw")

        # Update the "x=..., y=..." text when the data has potentially been changed
        if self.canvas_motion_event is not None:
            self.canvas.motion_notify_event(self.canvas_motion_event)

        self.update_help_text()
    

    # Enable and Disable are used to prevent the user from starting a new plot calculation
    # while there already is one underway. This is because we are not able to cancel the
    # execution of a calculation which is being done on the GPU.
    
    def disable(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.disable")
        if not isinstance(self.drawn_object, ScatterPlot):
            self.gui.set_user_controlled(False)
            self.hotkeys.disable()
        
    def enable(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.enable")
        if not isinstance(self.drawn_object, ScatterPlot):
            self.gui.set_user_controlled(True)
            self.hotkeys.enable()
