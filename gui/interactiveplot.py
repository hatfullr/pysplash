from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
    from keypresshandler import KeyPressHandler
else:
    import tkinter as tk
    from gui.keypresshandler import KeyPressHandler
import globals

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.image import AxesImage
import matplotlib.colorbar
import matplotlib.colors
import numpy as np
from copy import copy

from lib.scatterplot import ScatterPlot
from lib.integratedvalueplot import IntegratedValuePlot

class InteractivePlot(tk.Frame,object):
    def __init__(self,gui,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.__init__")
        self.gui = gui

        super(InteractivePlot,self).__init__(self.gui,*args,**kwargs)

        self.fig = Figure(figsize=(6,6),dpi=int(self.gui.dpi))
        self.ax = self.fig.add_subplot(111)

        self.x_cid = None
        self.y_cid = None
        
        self.cax = None
        self.colorbar = None
        self.cax_cid = None
        self.cbwidth = 0.025
        self.cbbuff = 0.01
        self.colorbar_visible = False
        
        self.drawn_object = None
        self.draw_type = 'None' # scatter

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.draw_enabled = False

        self.canvas.draw()
        
        self.winfo_toplevel().bind("<<ResizeStarted>>",self.disable_draw)
        self.winfo_toplevel().bind("<<ResizeStopped>>",self.enable_draw)
        self.canvas.get_tk_widget().bind("<<DataChanged>>",self.on_data_changed)

        self.keypresshandler = KeyPressHandler(self.canvas)
        self.keypresshandler.connect()

        self.keypresshandler.register('t',self.set_time_text)
        
        self.toggle_clim_adaptive()
        
        self.init_after_id = None
        
        self.wait_for_init()

    def wait_for_init(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.wait_for_init")
        if self.init_after_id is not None: self.after_cancel(self.init_after_id)
        if 'data' not in dir(self.gui):
            self.init_after_id = self.after(100,self.wait_for_init)
        else:
            self.initialize_drawn_object()
    
    def initialize_drawn_object(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.initialize_drawn_object")

        self.reset_data_xlim()
        self.reset_data_ylim()
        self.enable_draw()

    def create_variables(self):
        if globals.debug > 1: print("interactiveplot.create_variables")
        self.xycoords = tk.StringVar()
        self.point_size = tk.IntVar(value=1)
        self.time = tk.DoubleVar()
        
        self.time.trace('w',lambda event=None: self.set_time_text(event))
        
        self.connect_clim()

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

    def enable_draw(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.enable_draw")
        self.draw_enabled = True
        
    def disable_draw(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.disable_draw")
        self.draw_enabled = False

    def draw(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.draw")
        if self.draw_enabled: self.canvas.draw_idle()

    def set_draw_type(self,new_draw_type):
        if globals.debug > 1: print("interactiveplot.set_draw_type")
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
        x = self.gui.controls.x.get()
        y = self.gui.controls.y.get()
        if x in ['x','y','z'] and y in ['x','y','z']:
            aspect = 'equal'
        else:
            aspect = None
        
        self.reset() # Clear the current plot

        # Scatter plot
        if self.draw_type == 'None':
            self.hide_colorbar()
            self.drawn_object = ScatterPlot(
                self.ax,
                self.gui.get_display_data(x),
                self.gui.get_display_data(y),
                s=self.gui.controls.point_size,
                aspect=aspect,
            )
        
        # Column density plot
        elif self.draw_type == 'Column density':
            self.show_colorbar()
            
            if self.gui.controls.caxis_adaptive_limits.get():
                self.connect_clim()
            
            A = self.gui.get_data('rho')
            m = self.gui.get_data('m')
            h = self.gui.get_data('h')
            rho = self.gui.get_data('rho')

            idx = self.gui.get_data('u') != 0
            
            self.drawn_object = IntegratedValuePlot(
                self.ax,
                A[idx],
                self.gui.get_data(x)[idx],
                self.gui.get_data(y)[idx],
                m[idx],
                h[idx],
                rho[idx],
                [ # physical units
                    self.gui.get_physical_units('rho'),
                    self.gui.get_physical_units(x),
                    self.gui.get_physical_units(y),
                    self.gui.get_physical_units('m'),
                    self.gui.get_physical_units('h'),
                    self.gui.get_physical_units('rho'),
                ],
                [ # display units
                    self.gui.get_display_units('rho'),
                    self.gui.get_display_units(x),
                    self.gui.get_display_units(y),
                    self.gui.get_display_units('m'),
                    self.gui.get_display_units('h'),
                    self.gui.get_display_units('rho'),
                ],
                cmap=self.colorbar.cmap,
                xscale=self.gui.controls.xaxis_scale.get(),
                yscale=self.gui.controls.yaxis_scale.get(),
                cscale=self.gui.controls.caxis_scale.get(),
                aspect=aspect,
            )
            
            # Update the colorbar limits; automatically updates the plotted
            # color limits
            self.update_colorbar_clim()

        elif self.draw_type == 'Optical depth':
            self.show_colorbar()
            
            if self.gui.controls.caxis_adaptive_limits.get():
                self.connect_clim()
            
            A = self.gui.get_data('rho')*self.gui.get_data('opacity')
            x = self.gui.get_data(self.gui.controls.x.get())
            y = self.gui.get_data(self.gui.controls.y.get())
            m = self.gui.get_data('m')
            h = self.gui.get_data('h')
            rho = self.gui.get_data('rho')

            idx = self.gui.get_data('u') != 0
            
            self.drawn_object = IntegratedValuePlot(
                self.ax,
                A[idx],
                x[idx],
                y[idx],
                m[idx],
                h[idx],
                rho[idx],
                [ # physical units
                    self.gui.get_physical_units('rho')*self.gui.get_physical_units('opacity'),
                    self.gui.get_physical_units(self.gui.controls.x.get()),
                    self.gui.get_physical_units(self.gui.controls.y.get()),
                    self.gui.get_physical_units('m'),
                    self.gui.get_physical_units('h'),
                    self.gui.get_physical_units('rho'),
                ],
                [ # display units
                    self.gui.get_display_units('rho')*self.gui.get_display_units('opacity'),
                    self.gui.get_display_units(self.gui.controls.x.get()),
                    self.gui.get_display_units(self.gui.controls.y.get()),
                    self.gui.get_display_units('m'),
                    self.gui.get_display_units('h'),
                    self.gui.get_display_units('rho'),
                ],
                cmap=self.colorbar.cmap,
                xscale=self.gui.controls.xaxis_scale.get(),
                yscale=self.gui.controls.yaxis_scale.get(),
                cscale=self.gui.controls.caxis_scale.get(),
            )

            # Update the colorbar limits; automatically updates the plotted
            # color limits
            self.update_colorbar_clim()
            
        self.canvas.draw_idle()
        

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
        self.fig.canvas.draw_idle()

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

    def update_controls_xlim(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update_controls_xlim")
        xlim = self.ax.get_xlim()
        self.gui.controls.xaxis_limits_low.set(xlim[0])
        self.gui.controls.xaxis_limits_high.set(xlim[1])

    def update_controls_ylim(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.update_controls_ylim")
        ylim = self.ax.get_ylim()
        self.gui.controls.yaxis_limits_low.set(ylim[0])
        self.gui.controls.yaxis_limits_high.set(ylim[1])
    
    def toggle_xlim_adaptive(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.toggle_xlim_adaptive")
        if self.gui.controls.xaxis_adaptive_limits.get(): # Turn on adaptive limits
            self.update_controls_xlim()
            self.x_cid = self.ax.callbacks.connect("xlim_changed",self.update_controls_xlim)
        else: # Turn off adaptive limits
            if self.x_cid is not None:
                self.ax.callbacks.disconnect(self.x_cid)
                self.x_cid = None

    def toggle_ylim_adaptive(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.toggle_ylim_adaptive")
        if self.gui.controls.yaxis_adaptive_limits.get(): # Turn on adaptive limits
            self.update_controls_ylim()
            self.y_cid = self.ax.callbacks.connect("ylim_changed",self.update_controls_ylim)
        else: # Turn off adaptive limits
            if self.y_cid is not None:
                self.ax.callbacks.disconnect(self.y_cid)
                self.y_cid = None
            
        
    def toggle_clim_adaptive(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.toggle_clim_adaptive")
        if self.gui.controls.caxis_adaptive_limits.get(): # Turn off adaptive limits
            self.disconnect_clim()
            # Set the user's entry boxes to be the current clim
            if self.colorbar_visible:
                clim = self.cax.get_ylim()
                self.gui.controls.caxis_limits_low.set(clim[0])
                self.gui.controls.caxis_limits_high.set(clim[1])
        else: # Turn on adaptive limits
            if self.cax is not None:
                self.connect_clim()
                self.update_colorbar_clim()
                self.canvas.draw_idle()
    
    def on_data_changed(self,*args,**kwargs):
        if globals.debug > 1: print("interactiveplot.on_data_changed")
        if isinstance(self.drawn_object,IntegratedValuePlot):
            self.update_colorbar_clim()
        self.canvas.draw_idle()

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

    def get_data_xlim(self,*args,**kwargs):
        x = self.gui.get_display_data(self.gui.controls.x.get())
        xmin = np.amin(x)
        xmax = np.amax(x)
        xmargin = self.ax.margins()[0]
        dx = (xmax-xmin)*xmargin
        return (xmin-dx, xmax+dx)
    def get_data_ylim(self,*args,**kwargs):
        y = self.gui.get_display_data(self.gui.controls.y.get())
        ymin = np.amin(y)
        ymax = np.amax(y)
        ymargin = self.ax.margins()[1]
        dy = (ymax-ymin)*ymargin
        return (ymin-dy, ymax+dy)
                      
        
    def reset_data_xlim(self,*args,**kwargs):
        self.ax.set_xlim(self.get_data_xlim())
    
    def reset_data_ylim(self,*args,**kwargs):
        self.ax.set_ylim(self.get_data_ylim())

    def reset_data_xylim(self,*args,**kwargs):
        if hasattr(self.gui, "data"):
            new_xlim = np.array(self.get_data_xlim())
            new_ylim = np.array(self.get_data_ylim())
            if self.drawn_object is not None:
                if self.drawn_object.aspect == 'equal':
                    new_xlim, new_ylim = self.drawn_object.equalize_aspect_ratio(xlim=new_xlim,ylim=new_ylim)
            xlim = np.array(self.ax.get_xlim())
            ylim = np.array(self.ax.get_ylim())

            if any(np.abs((new_xlim-xlim)/xlim) > 0.001): self.ax.set_xlim(new_xlim)
            if any(np.abs((new_ylim-ylim)/ylim) > 0.001): self.ax.set_ylim(new_ylim)
            self.canvas.draw_idle()
                         
