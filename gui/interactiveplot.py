from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    from keypresshandler import KeyPressHandler
else:
    import tkinter as tk
    from gui.keypresshandler import KeyPressHandler
import globals

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection, PolyCollection
import matplotlib.colorbar
import matplotlib.colors
import numpy as np
from copy import copy

from lib.scatterplot import ScatterPlot
from lib.integratedvalueplot import IntegratedValuePlot
from lib.orientationarrows import OrientationArrows
from lib.customaxesimage import CustomAxesImage
from lib.customcolorbar import CustomColorbar

class InteractivePlot(tk.Frame,object):
    def __init__(self,master,gui,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.__init__")
        self.gui = gui

        super(InteractivePlot,self).__init__(master,*args,**kwargs)

        self.fig = Figure(figsize=(6,6),dpi=int(self.gui.dpi))
        self.ax = self.fig.add_subplot(111)

        self.x_cid = None
        self.y_cid = None

        self.orientation = OrientationArrows(self.gui,self.ax)
        
        #self.cax = None
        self.colorbar = CustomColorbar(self.ax)
        #self.cax_cid = None
        #self.cbwidth = 0.025
        #self.cbbuff = 0.01
        #self.colorbar_visible = False
        
        self.drawn_object = None

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.draw_enabled = False

        self.previous_args = None
        self.previous_kwargs = None
        self.previous_xlim = None
        self.previous_ylim = None

        self.keypresshandler = KeyPressHandler(self.canvas)
        self.keypresshandler.connect()

        self.keypresshandler.register('t',self.set_time_text)
        
    def create_variables(self):
        if globals.debug > 1: print("interactiveplot.create_variables")
        self.xycoords = tk.StringVar()
        self.point_size = tk.IntVar(value=1)
        self.time = tk.DoubleVar()
        
        self.time.trace('w',lambda event=None: self.set_time_text(event))

        self.time_text = None
    
    def create_widgets(self):
        if globals.debug > 1: print("interactiveplot.create_widgets")
        self.canvas = FigureCanvasTkAgg(self.fig,master=self)
        self.xycoords_label = tk.Label(self,textvariable=self.xycoords,bg='white')
        
    def place_widgets(self):
        if globals.debug > 1: print("interactiveplot.place_widgets")
        self.canvas.get_tk_widget().grid(row=0,sticky='news')
        self.xycoords_label.place(in_=self.canvas.get_tk_widget(),relx=1,rely=1,anchor='se')

        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.reset")
        if self.drawn_object is not None:
            self.drawn_object.remove()
            self.drawn_object = None
    
    def update(self,*args, **kwargs):
        if globals.debug > 1:
            print("interactiveplot.update")
            print("    self.ax = ",self.ax)

        self.gui.set_user_controlled(False)
        x = self.gui.controls.axis_controllers['XAxis'].value.get()
        y = self.gui.controls.axis_controllers['YAxis'].value.get()
        if x in ['x','y','z'] and y in ['x','y','z']:
            aspect = 'equal'
        else:
            aspect = None

        # If there's no data to plot, stop here
        if not self.gui.data:
            self.canvas.draw_idle()
            self.gui.set_user_controlled(True)
            return

        
        kwargs = {}
        kwargs['xscale'] = self.gui.controls.axis_controllers['XAxis'].scale.get()
        kwargs['yscale'] = self.gui.controls.axis_controllers['YAxis'].scale.get()
        kwargs['xunits'] = self.gui.controls.axis_controllers['XAxis'].units.value.get()
        kwargs['yunits'] = self.gui.controls.axis_controllers['YAxis'].units.value.get()

        colorbar_text = self.gui.controls.axis_controllers['Colorbar'].value.get()
        
        # Scatter plot
        if not colorbar_text.strip() or colorbar_text.strip() == "":
            if self.gui.data.is_image:
                method = CustomAxesImage
                args = (
                    self.ax,
                    self.gui.data,
                )
                kwargs['aspect'] = aspect
                self.colorbar.show()
            else:
                method = ScatterPlot
                args = (
                    self.ax,
                    self.gui.get_display_data(x),
                    self.gui.get_display_data(y),
                )
                kwargs['s'] = self.gui.controls.plotcontrols.point_size.get()
                kwargs['aspect'] = aspect
                self.colorbar.hide()

        elif colorbar_text.strip() or colorbar_text.strip() != "":
            A, Ap, Ad = self.gui.controls.axis_controllers['Colorbar'].entry.get_data()
            if A is None or Ap is None or Ad is None:
                raise Exception("One of A, Ap, or Ad was None. This should never happen.")
            
            m = self.gui.get_display_data('m')
            h = self.gui.get_display_data('h')
            rho = self.gui.get_display_data('rho')

            idx = self.gui.get_data('u') != 0

            method = IntegratedValuePlot
            args = (
                self.ax,
                A[idx],
                self.gui.get_display_data(x)[idx],
                self.gui.get_display_data(y)[idx],
                m[idx],
                h[idx],
                rho[idx],
                [ # physical units
                    Ap,
                    self.gui.get_physical_units(x),
                    self.gui.get_physical_units(y),
                    self.gui.get_physical_units('m'),
                    self.gui.get_physical_units('h'),
                    self.gui.get_physical_units('rho'),
                ],
                [ # display units
                    Ad,
                    self.gui.get_display_units(x),
                    self.gui.get_display_units(y),
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
        else:
            raise Exception("Unable to decide on scatter plot or integrated value plot. This should never happen.")

        changed_args = False
        
        # If the plot we are going to make is the same as the plot already
        # on the canvas, then don't draw a new one
        if self.drawn_object is not None and self.previous_args is not None:
            xmin,xmax = self.ax.get_xlim()
            ymin,ymax = self.ax.get_ylim()
            #vmin,vmax = self.colorbar.vmin, self.colorbar.vmax
            #xmin,xmax,ymin,ymax = self.drawn_object._extent
            if (self.previous_xlim[0] == xmin and
                self.previous_xlim[1] == xmax and
                self.previous_ylim[0] == ymin and
                self.previous_ylim[1] == ymax):
                kwargs['initialize'] = False
                
                if len(args) == len(self.previous_args):
                    # We break out of this for-loop if any of the current arguments
                    # have changed compared to the previous arguments
                    for arg in args:
                        for prev_arg in self.previous_args:
                            try:
                                if arg == prev_arg: break
                            except ValueError:
                                if np.array_equal(arg,prev_arg):
                                    break
                        else:
                            changed_args = True
                            break
                    else: # The args are the same as before
                        keys = self.previous_kwargs.keys()
                        if len(keys) == len(kwargs.keys()):
                            for key,val in kwargs.items():
                                if key not in keys or self.previous_kwargs[key] != val:
                                    break
                            else:
                                self.gui.set_user_controlled(True)
                                print("   all args and kwargs were the same as the previous plot")
                                print("   ",args)
                                print("   ",self.previous_args)
                                print("   ",kwargs)
                                print("   ",self.previous_kwargs)
                                return

        # We only get here if the plot we are going to draw won't be
        # the same as the previous plot
        
        
        if self.drawn_object is None:
            kwargs['initialize'] = True

        if changed_args: self.reset() # Clear the current plot

        # Update the orientation
        if self.gui.controls.plotcontrols.show_orientation.get():
            self.orientation.draw()
        else:
            self.orientation.clear()

        self.drawn_object = method(*args,**kwargs)
        
        if globals.use_multiprocessing_on_scatter_plots:
            if self.drawn_object.thread is None:
                raise RuntimeError("Failed to spawn thread to draw the plot")
            
        # After creation
        if not self.gui.data.is_image:

            self.previous_args = args
            self.previous_kwargs = kwargs            
        
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

            if self.colorbar.visible and (cadaptive or np.nan in controls_climits):
                self.reset_clim(draw=False)
                

        self.previous_xlim = self.ax.get_xlim()
        self.previous_ylim = self.ax.get_ylim()
        self.previous_vmin = self.colorbar.vmin
        self.previous_vmax = self.colorbar.vmax

        # Put the filename in the axis title for now
        f = self.gui.filecontrols.current_file.get()
        if len(f) > 30:
            f = "..."+f[-27:]
        self.ax.set_title(f)
        
        self.gui.set_user_controlled(True)
        
    def set_time_text(self,event):
        if globals.debug > 1: print("interactiveplot.set_time_text")
        text = "t = %f" % self.time.get()
        
        if self.time_text is None:
            self.time_text = self.ax.annotate(
                text,
                (event.x,event.y),
                xycoords='figure pixels',
            )
        else:
            pos = self.time_text.get_position()
            if event.x == pos[0] and event.y == pos[1] and self.time_text.get_visible():
                self.time_text.set_visible(False)
            else:
                self.time_text.set_text(text)
                self.time_text.set_position((event.x,event.y))
                self.time_text.set_visible(True)
        self.canvas.draw_idle()

    def reset_clim(self, draw=True):
        if globals.debug > 1: print("interactiveplot.reset_clim")
        self.canvas.draw() # I don't understand why we need to do this, but it works when we do...
        newlim = np.array(self.colorbar.calculate_limits(data=self.drawn_object._data))
        lim = np.array([self.colorbar.vmin, self.colorbar.vmax])
        if None not in newlim:
            if any(np.abs((newlim-lim[lim != 0])/lim[lim != 0]) > 0.001):
                self.colorbar.set_clim(newlim)
                self.gui.controls.axis_controllers['Colorbar'].limits.on_axis_limits_changed()
        if draw: self.canvas.draw_idle()

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
        
    def calculate_xylim(self, which='both'):
        if globals.debug > 1: print("interactiveplot.calculate_xylim")

        if which not in ['xlim', 'ylim', 'both']:
            raise ValueError("Keyword 'which' must be one of 'xlim', 'ylim', or 'both'. Received ",which)

        new_xlim = [None, None]
        new_ylim = [None, None]
        
        if hasattr(self.gui, "data") and self.gui.data:
            x = self.gui.controls.axis_controllers['XAxis'].value.get()
            y = self.gui.controls.axis_controllers['YAxis'].value.get()
            xdata = self.gui.get_display_data(x)
            ydata = self.gui.get_display_data(y)
            xdata = xdata[np.isfinite(xdata)]
            ydata = ydata[np.isfinite(ydata)]
            new_xlim = np.array([np.nanmin(xdata), np.nanmax(xdata)])
            new_ylim = np.array([np.nanmin(ydata), np.nanmax(ydata)])
        else:
            # Get the home view and use its limits as the new limits
            xmin, xmax, ymin, ymax = self.gui.plottoolbar.get_home_xylimits()
            new_xlim = np.array([xmin, xmax])
            new_ylim = np.array([ymin, ymax])
        
        xmargin, ymargin = self.ax.margins()
        dx = new_xlim[1]-new_xlim[0]
        dy = new_ylim[1]-new_ylim[0]
        new_xlim = np.array([new_xlim[0]-dx*xmargin,new_xlim[1]+dx*xmargin])
        new_ylim = np.array([new_ylim[0]-dy*ymargin,new_ylim[1]+dy*ymargin])
            
        # Apply the units to the limits
        xunits = self.gui.controls.axis_controllers['XAxis'].units.value.get()
        yunits = self.gui.controls.axis_controllers['YAxis'].units.value.get()
        
        new_xlim /= xunits
        new_ylim /= yunits
            
        if which == 'xlim': return new_xlim, [None, None]
        elif which == 'ylim': return [None, None], new_ylim
        else: return new_xlim, new_ylim
        

