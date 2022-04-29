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
        self.draw_type = 'None' # scatter

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
        
        self.init_after_id = None
    
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

    def set_draw_type(self,new_draw_type):
        if globals.debug > 1: print("interactiveplot.set_draw_type")
        self.draw_type = new_draw_type

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

        # Scatter plot
        if self.draw_type == 'None':
            if self.gui.data.is_image:
                method = CustomAxesImage
                args = (
                    self.ax,
                    self.gui.data,
                )
                kwargs['aspect'] = aspect
                self.reset_data_xylim()
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

        else: # It will be some form of IntegratedValue plot
            if self.draw_type == 'Column density':
                A = self.gui.get_data('rho')
                Ap = self.gui.get_physical_units('rho')
                Ad = self.gui.get_display_units('rho')
            elif self.draw_type == 'Optical depth':
                A = self.gui.get_data('rho')*self.gui.get_data('opacity')
                Ap = self.gui.get_physical_units('rho')*self.gui.get_physical_units('opacity')
                Ad = self.gui.get_display_units('rho')*self.gui.get_display_units('opacity')
            
            m = self.gui.get_data('m')
            h = self.gui.get_data('h')
            rho = self.gui.get_data('rho')

            idx = self.gui.get_data('u') != 0

            method = IntegratedValuePlot
            args = (
                self.ax,
                A[idx],
                self.gui.get_data(x)[idx],
                self.gui.get_data(y)[idx],
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
                ]
            )

            kwargs['cmap'] = self.colorbar.cmap
            kwargs['cscale'] = self.gui.controls.axis_controllers['Colorbar'].scale.get()
            kwargs['aspect'] = aspect
            kwargs['colorbar'] = self.colorbar

            self.colorbar.show()

        changed_args = False
        
        # If the plot we are going to make is the same as the plot already
        # on the canvas, then don't draw a new one
        if self.drawn_object is not None and self.previous_args is not None:
            xmin,xmax = self.ax.get_xlim()
            ymin,ymax = self.ax.get_ylim()
            vmin,vmax = self.colorbar.vmin, self.colorbar.vmax
            #xmin,xmax,ymin,ymax = self.drawn_object._extent
            if (self.previous_xlim[0] == xmin and
                self.previous_xlim[1] == xmax and
                self.previous_ylim[0] == ymin and
                self.previous_ylim[1] == ymax and
                self.previous_vmin == vmin and
                self.previous_vmax == vmax):
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
            else:
                # Block until the plot is finished drawing
                while self.drawn_object.thread.isAlive():
                    self.winfo_toplevel().update()

                # Update the controls' axis limits
                for axis_controller in self.controls.axis_controllers:
                    axis_controller.limits.on_axis_limits_changed()

                self.controls.save_state()
        
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
                (yadaptive or np.nan in controls_ylimits)): self.reset_data_xylim(which='both',draw=False)
            elif xadaptive or np.nan in controls_xlimits: self.reset_data_xylim(which='xlim',draw=False)
            elif yadaptive or np.nan in controls_ylimits: self.reset_data_xylim(which='ylim',draw=False)

            if (cadaptive or np.nan in controls_climits): self.reset_colorbar_limits(draw=False)
            
        #self.canvas.draw_idle()
        self.previous_xlim = self.ax.get_xlim()
        self.previous_ylim = self.ax.get_ylim()
        self.previous_vmin = self.colorbar.vmin
        self.previous_vmax = self.colorbar.vmax

        self.gui.set_user_controlled(True)

    def on_point_size_changed(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.on_point_size_changed")
        if isinstance(self.drawn_object,ScatterPlot):
            self.drawn_object.set_size(self.gui.controls.plotcontrols.point_size)

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

    def on_data_changed(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.on_data_changed")
        if isinstance(self.drawn_object,IntegratedValuePlot):
            self.update_colorbar_clim()
            self.canvas.draw_idle()
    """
    def update_colorbar_label(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update_colorbar_label")
        if self.drawn_object is None: return
        if not hasattr(self.drawn_object,"cscale"): return

        label = self.draw_type
        if self.drawn_object.cscale == 'log10':
            label = "$\\log_{10}$ "+label
        elif self.drawn_object.cscale == '^10':
            label = "$10^{\\mathrm{"+label.replace(" ","\\ ")+"}}$"
        
        self.colorbar.set_label(label)
        #self.colorbar.draw_all()
    """
    
    def get_data_xlim(self,*args,**kwargs):
        x = self.gui.get_display_data(self.gui.controls.axis_controllers['XAxis'].value.get(), scaled = False)
        xmin = np.amin(x)
        xmax = np.amax(x)
        xmargin = self.ax.margins()[0]
        dx = (xmax-xmin)*xmargin
        return (xmin-dx, xmax+dx)
    def get_data_ylim(self,*args,**kwargs):
        y = self.gui.get_display_data(self.gui.controls.axis_controllers['YAxis'].value.get(), scaled = False)
        ymin = np.amin(y)
        ymax = np.amax(y)
        ymargin = self.ax.margins()[1]
        dy = (ymax-ymin)*ymargin
        return (ymin-dy, ymax+dy)

    def reset_data_xylim(self,which='both',draw=True):
        if globals.debug > 1: print("interactiveplot.reset_data_xylim")
        
        new_xlim, new_ylim = self.calculate_data_xylim(which=which)

        xlim = np.array(self.ax.get_xlim())
        ylim = np.array(self.ax.get_ylim())
        
        if None not in new_xlim:
            if any(np.abs((new_xlim-xlim)/xlim) > 0.001):
                self.ax.set_xlim(new_xlim)
                self.gui.controls.axis_controllers['XAxis'].limits.on_axis_limits_changed()
        if None not in new_ylim:
            if any(np.abs((new_ylim-ylim)/ylim) > 0.001):
                self.ax.set_ylim(new_ylim)
                self.gui.controls.axis_controllers['YAxis'].limits.on_axis_limits_changed()
            
        if draw: self.canvas.draw_idle()

    def reset_colorbar_limits(self, draw=True):
        if globals.debug > 1: print("interactiveplot.reset_colorbar_limits")
        
        new_vmin, new_vmax = self.colorbar.calculate_limits()
        
        vmin = self.colorbar.vmin
        vmax = self.colorbar.vmax
        limits_changed = False
        if vmin:
            if np.abs((new_vmin-vmin)/vmin) > 0.001:
                self.colorbar.vmin = new_vmin
                limits_changed = True
        if vmax:
            if np.abs((new_vmax-vmax)/vmax) > 0.001:
                self.colorbar.vmax = new_vmax
                limits_changed = True

        if limits_changed:
            self.colorbar.set_clim(self.colorbar.vmin, self.colorbar.vmax)
            self.gui.controls.axis_controllers['Colorbar'].limits.on_axis_limits_changed()

        if draw: self.canvas.draw_idle()
        
        
    def calculate_data_xylim(self, which='both'):
        if globals.debug > 1: print("interactiveplot.calculate_data_xylim")

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
            new_xlim = [np.nanmin(xdata), np.nanmax(xdata)]
            new_ylim = [np.nanmin(ydata), np.nanmax(ydata)]
        else:
            # Get the home view and use its limits as the new limits
            xmin, xmax, ymin, ymax = self.gui.plottoolbar.get_home_xylimits()
            new_xlim = [xmin, xmax]
            new_ylim = [ymin, ymax]
        if which == 'xlim': return new_xlim, [None, None]
        elif which == 'ylim': return [None, None], new_ylim
        else: return new_xlim, new_ylim
        
