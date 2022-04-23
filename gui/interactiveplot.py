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
    def __init__(self,gui,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.__init__")
        self.gui = gui

        super(InteractivePlot,self).__init__(self.gui,*args,**kwargs)

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

        #self.winfo_toplevel().bind("<<ResizeStarted>>",self.disable_draw)
        #self.winfo_toplevel().bind("<<ResizeStopped>>",self.enable_draw)

        self.keypresshandler = KeyPressHandler(self.canvas)
        self.keypresshandler.connect()

        self.keypresshandler.register('t',self.set_time_text)
        
        self.init_after_id = None
    
    def initialize_drawn_object(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.initialize_drawn_object")
        self.reset_data_xlim(draw=False)
        self.reset_data_ylim(draw=False)
        self.enable_draw()
        self.update()

    def create_variables(self):
        if globals.debug > 1: print("interactiveplot.create_variables")
        self.xycoords = tk.StringVar()
        self.point_size = tk.IntVar(value=1)
        self.time = tk.DoubleVar()
        
        self.time.trace('w',lambda event=None: self.set_time_text(event))
        
        #self.connect_clim()

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
        print("     ",self.draw_type,new_draw_type)
        self.draw_type = new_draw_type

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.reset")
        if self.drawn_object is not None:
            self.drawn_object.remove()
            self.drawn_object = None
    
    def update(self,*args,**kwargs):
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
        
        # Update the orientation
        if self.gui.controls.show_orientation.get():
            self.orientation.draw()
        else:
            self.orientation.clear()

        # If there's no data to plot, stop here
        if self.gui.data is None:
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
                kwargs['s'] = self.gui.controls.point_size.get()
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


        # If the plot we are going to make is the same as the plot already
        # on the canvas, then don't draw a new one
        if self.drawn_object is not None and self.previous_args is not None:
            xmin,xmax = self.ax.get_xlim()
            ymin,ymax = self.ax.get_ylim()
            #xmin,xmax,ymin,ymax = self.drawn_object._extent
            if (self.previous_xlim[0] == xmin and
                self.previous_xlim[1] == xmax and
                self.previous_ylim[0] == ymin and
                self.previous_ylim[1] == ymax):
                kwargs['initialize'] = False
                
                if len(args) == len(self.previous_args):
                    for arg in args:
                        for prev_arg in self.previous_args:
                            try:
                                if arg == prev_arg:
                                    break
                            except ValueError:
                                if np.array_equal(arg,prev_arg):
                                    break
                        else:
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
            first_plot = True
            kwargs['initialize'] = True
        else:
            first_plot = False
            self.reset() # Clear the current plot

        self.drawn_object = method(*args,**kwargs)
        
        if globals.use_multiprocessing_on_scatter_plots:
            if self.drawn_object.thread is None:
                raise RuntimeError("Failed to spawn thread to draw the plot")
            else:
                # Block until the plot is finished drawing
                while self.drawn_object.thread.isAlive():
                    self.update()

                # Update the controls' axis limits
                for axis_controller in self.controls.axis_controllers:
                    axis_controller.update_limits()

                # Connect the controls to the interative plot
                #self.gui.controls.connect()
                self.controls.save_state()
        
        # After creation
        if not self.gui.data.is_image:
            if self.draw_type != 'None':
                # Update the colorbar limits; automatically updates the plotted
                # color limits
                #self.colorbar.update_limits()
                pass

            self.previous_args = args
            self.previous_kwargs = kwargs            
        
            xadaptive = self.gui.controls.axis_controllers['XAxis'].is_adaptive.get()
            yadaptive = self.gui.controls.axis_controllers['YAxis'].is_adaptive.get()
            cadaptive = self.gui.controls.axis_controllers['Colorbar'].is_adaptive.get()

            controls_xlimits = [
                self.gui.controls.axis_controllers['XAxis'].limits_low.get(),
                self.gui.controls.axis_controllers['XAxis'].limits_high.get(),
            ]
            controls_ylimits = [
                self.gui.controls.axis_controllers['YAxis'].limits_low.get(),
                self.gui.controls.axis_controllers['YAxis'].limits_high.get(),
            ]
            
            if ((xadaptive or np.nan in controls_xlimits) and
                (yadaptive or np.nan in controls_ylimits)): self.reset_data_xylim(which='both',draw=False)
            elif xadaptive or np.nan in controls_xlimits: self.reset_data_xylim(which='xlim',draw=False)
            elif yadaptive or np.nan in controls_ylimits: self.reset_data_xylim(which='ylim',draw=False)
            
        #self.canvas.draw_idle()
        self.previous_xlim = self.ax.get_xlim()
        self.previous_ylim = self.ax.get_ylim()

        self.gui.set_user_controlled(True)


        
                    

    def on_point_size_changed(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.on_point_size_changed")
        if isinstance(self.drawn_object,ScatterPlot):
            self.drawn_object.set_size(self.gui.controls.point_size)

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
        
    """
    def init_colorbar(self):
        if globals.debug > 1: print("interactiveplot.init_colorbar")
        d = self.cbwidth + self.cbbuff
        
        pos = self.ax.get_position()
        self.cax = self.fig.add_axes([
            pos.x1-self.cbwidth - 0.1,
            pos.y0 + 0.5*d,
            self.cbwidth,
            pos.height - 0.5*d,
        ],visible=False)
        
        self.cax.yaxis.tick_right()
        
        self.colorbar = matplotlib.colorbar.ColorbarBase(self.cax)

    
    def show_colorbar(self):
        if globals.debug > 1: print("interactiveplot.show_colorbar")
        if self.cax is None: self.init_colorbar()
        if self.cax.get_visible(): return
        
        pos = self.ax.get_position()
        
        d = self.cbbuff + self.cbwidth
        
        self.ax.set_position([
            pos.x0,
            pos.y0 + 0.5*d,
            pos.width - d - 0.1,
            pos.height - 0.5*d,
        ])

        self.cax.set_visible(True)

        # Enable the colorbar scale controls
        self.gui.controls.enable('colorbar')
        
        self.colorbar_visible = True
        self.update_colorbar_label()

    def hide_colorbar(self):
        if globals.debug > 1: print("interactiveplot.hide_colorbar")
        if self.cax is None: return
        if not self.cax._visible: return
        
        self.disconnect_clim()
        
        pos = self.ax.get_position()
        
        d = self.cbbuff + self.cbwidth
        
        self.ax.set_position([
            pos.x0,
            pos.y0 - 0.5*d,
            pos.width + d,
            pos.height + 0.5*d
        ])
        
        self.cax.set_visible(False)

        # Disable the colorbar controls
        self.gui.controls.caxis_scale.set('linear')
        self.gui.controls.disable('colorbar')

        self.colorbar_visible = False
        
    def update_colorbar_clim(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update_colorbar_clim")
        if self.gui.controls.caxis_adaptive_limits.get():
            if self.drawn_object is not None:
                data = self.drawn_object._data
                vmin = np.nanmin(data[np.isfinite(data)])
                vmax = np.nanmax(data[np.isfinite(data)])
                self.colorbar.norm = matplotlib.colors.Normalize(vmin=vmin,vmax=vmax)
                self.colorbar.draw_all()
                # Update the values in the control panel
                self.gui.controls.caxis_limits_low.set(vmin)
                self.gui.controls.caxis_limits_high.set(vmax)
        else:
            # Make sure the colorbar limits match what is in the controls panel
            ylim = [
                self.gui.controls.caxis_limits_low.get(),
                self.gui.controls.caxis_limits_high.get(),
            ]
            if ylim[0] != self.cax.get_ylim()[0] or ylim[1] != self.cax.get_ylim()[1]:
                data = self.drawn_object._data
                self.colorbar.norm = matplotlib.colors.Normalize(vmin=ylim[0],vmax=ylim[1])
                self.colorbar.draw_all()
                self.canvas.draw_idle()
                
    def update_data_clim(self,axis=None,ylim=None):
        if globals.debug > 1: print("interactiveplot.update_data_clim")
        if self.drawn_object is not None:
            if ylim is None: ylim = self.cax.get_ylim()
            self.drawn_object.set_clim(ylim)
    
    def connect_clim(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.connect_clim")
        if self.cax is not None: self.cax_cid = self.cax.callbacks.connect('ylim_changed',self.update_data_clim)
    
    def disconnect_clim(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.disconnect_clim")
        if self.cax_cid is not None:
            self.cax.callbacks.disconnect(self.cax_cid)
            self.cax_cid = None
    """
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
            if any(np.abs((new_xlim-xlim)/xlim) > 0.001): self.ax.set_xlim(new_xlim)
        if None not in new_ylim:
            if any(np.abs((new_ylim-ylim)/ylim) > 0.001): self.ax.set_ylim(new_ylim)

        self.gui.controls.axis_controllers['XAxis'].update_limits()
        self.gui.controls.axis_controllers['YAxis'].update_limits()
            
        if draw: self.canvas.draw_idle()
        
    def calculate_data_xylim(self, which='both'):
        if globals.debug > 1: print("interactiveplot.calculate_data_xylim")

        if which not in ['xlim', 'ylim', 'both']:
            raise ValueError("Keyword 'which' must be one of 'xlim', 'ylim', or 'both'. Received ",which)

        new_xlim = [None, None]
        new_ylim = [None, None]
        
        if hasattr(self.gui, "data"):
            if self.gui.data.is_image:
                new_xlim = self.gui.data['extent'][:2]
                new_ylim = self.gui.data['extent'][-2:]
            else:
                new_xlim = np.array(self.get_data_xlim())
                new_ylim = np.array(self.get_data_ylim())
                if self.drawn_object is not None:
                    if self.drawn_object.aspect == 'equal':
                        new_xlim, new_ylim = self.drawn_object.equalize_aspect_ratio(xlim=new_xlim,ylim=new_ylim)
        if which == 'xlim': return new_xlim, [None, None]
        elif which == 'ylim': return [None, None], new_ylim
        else: return new_xlim, new_ylim
