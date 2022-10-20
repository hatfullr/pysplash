import matplotlib.colorbar
from matplotlib.image import AxesImage
import matplotlib.colors
import matplotlib.image
import globals
import numpy as np

class CustomColorbar(matplotlib.colorbar.ColorbarBase,object):
    def __init__(self,ax,width=0.025,pad=[0.01,0.1],side='right'):
        if globals.debug > 1: print("customcolorbar.__init__")
        # ax is what the colorbar is attached to
        self._ax = ax
        self.width = width
        if not isinstance(pad,(list,tuple,np.ndarray)): self.pad = [pad,pad]
        else: self.pad = pad
        self.side = side
        
        # Create the cax
        self.cax = self._ax.get_figure().add_axes([0,0,0,0],visible=False)
        
        super(CustomColorbar,self).__init__(self.cax)

        self.previous_ax_position = None
        
        self.show_cid = None
        self.image_cid = None
        self.draw_cid = None
        self.connected_canvas = None
        self.axis_controller = None
        self.linear_data = []

        self.axesimages = []

        self._after_update_axesimage_clim_cid = None
        self._after_limits_changed_cid = None
        self._axesimages_cids = []

    @property
    def visible(self):
        return self.cax.get_visible()

    @visible.setter
    def visible(self, value):
        if value != self.cax.get_visible():
            self.cax.set_visible(value)
            if self.connected: self.connected_canvas.draw_idle()
    @property
    def connected(self): return self.connected_canvas is not None

    @property
    def data(self):
        if self.axis_controller is None:
            raise Exception("cannot access data while axis_controller is not connected")
        # Modify by the units
        units = self.axis_controller.units.value.get()
        data = self.linear_data
        for i,d in enumerate(data):
            # Modify by the scale
            scale = self.axis_controller.scale.get()
            if scale == 'log10': data[i] = np.log10(d)
            elif scale == '10^': data[i] = 10**d
        return data

    @property
    def axesimage_connected(self): return len(self.axesimages) > 0

    @property
    def axiscontroller_connected(self): return hasattr(self, "axis_controller") and self.axis_controller is not None
    
    def set_clim(self, cminmax):
        if globals.debug > 1: print("customcolorbar.set_clim")
        if None not in cminmax:
            lim = self.get_cax_limits()
            self.vmin = cminmax[0]
            self.vmax = cminmax[1]
            self.norm = matplotlib.colors.Normalize(vmin=self.vmin,vmax=self.vmax)
            
            # Implicitly calls update_axesimage_clim when cax limits are modified
            if self.side in ['right', 'left']:
                self.cax.set_ylim(self.vmin,self.vmax)
            elif self.side in ['top', 'bottom']:
                self.cax.set_xlim(self.vmin,self.vmax)
            else:
                raise Exception("expected one of 'left', 'right', 'top', or 'bottom' for colorbar side but got '"+str(self.side)+"'")
                
            self.draw_all()
    
    def find_axesimage(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.find_axesimage")
        for child in self._ax.get_children():
            if isinstance(child, AxesImage):
                return child
        return None
    
    """
    def calculate_limits(self,data=None,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.calculate_limits")
        if self.visible:
            # Get the color data in the plot
            vmin,vmax = None, None
            if data is None:
                axesimage = self.find_axesimage()
                if axesimage:
                    data = axesimage.get_array()
                # Point density plots always range between 0 and 1,
                # except when it's on a log scale (not supported yet)
                from lib.pointdensityplot import PointDensityPlot
                if isinstance(axesimage, PointDensityPlot):
                    vmin, vmax = 0., 1.

            if data is None:
                return [None, None]

            finite_data = data[np.isfinite(data)]
            if vmin is None: vmin = np.nanmin(finite_data)
            if vmax is None: vmax = np.nanmax(finite_data)
            return [vmin, vmax]
        else: return [None, None]
    """

    def update_limits(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_limits")
        self.set_clim(self.calculate_limits())

    def connect_canvas(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.connect_canvas")
        self.connected_canvas = self._ax.get_figure().canvas
        self.connect_resize()
        self.connect_draw()
        
        if self.side in ['right', 'left']:
            self.image_cid = self.cax.callbacks.connect(
                "ylim_changed",
                self.update_axesimage_clim,
            )
        elif self.side in ['top', 'bottom']:
            self.image_cid = self.cax.callbacks.connect(
                "xlim_changed",
                self.update_axesimage_clim,
            )
        else: raise ValueError("Colorbar has an invalid side '",self.side,"'")

    def disconnect_canvas(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_canvas")
        self.disconnect_resize()
        self.disconnect_axesimages()
        #self.disconnect_draw()
        self.connected_canvas = None
        if self.image_cid is not None:
            self.cax.callbacks.disconnect(self.image_cid)
        self.image_cid = None

    
    def connect_draw(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.connect_draw")
        self.draw_cid = self.connected_canvas.mpl_connect("draw_event",self.on_draw)
    def disconnect_draw(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_draw")
        if self.draw_cid is not None:
            self.connected_canvas.mpl_disconnect(self.draw_cid)
        self.draw_cid = None

    def on_draw(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.on_draw")
        self.update_position()

    def connect_resize(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.connect_resize")
        self.show_cid = self.connected_canvas.mpl_connect("resize_event",self.update_position)
    def disconnect_resize(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_resize")
        if self.show_cid is not None:
            self.connected_canvas.mpl_disconnect(self.show_cid)
        self.show_cid = None

    def connect_controller(self, axis_controller):
        if globals.debug > 1: print("customcolorbar.connect_controller")
        if self.axis_controller is None:
            self.axis_controller = axis_controller
        else:
            raise Exception("cannot connect colorbar '"+str(self)+"' to axis_controller '"+str(axis_controller)+"' because it is already connected to '"+str(self.axis_controller)+"'")
        
        # Override what the adaptive limits button does
        self.axis_controller.limits.configure(adaptivecommands=(self.set_adaptive_limits,None))
        
        # When the AxisScale buttons are clicked
        self.axis_controller.bind("<<OnScaleChanged>>", self.on_scale_changed, add="+")
        # Right before drawing the AxesImage, grab its data
        self.axis_controller.gui.bind("<<PlotUpdate>>", self.update_data, add="+")
        for var in [self.axis_controller.limits.low, self.axis_controller.limits.high]:
            if var in globals.state_variables: globals.state_variables.remove(var)
        
        # Whenever the limits in the axis controller are edited, update the plot
        self.axis_controller.limits.low.trace('w', self.on_axis_controller_limits_changed)
        self.axis_controller.limits.high.trace('w', self.on_axis_controller_limits_changed)

    # When an AxesImage is created, we connect this colorbar to it
    # by calling this function. When the AxesImage is removed from
    # the plot, disconnect_axesimage is called.
    def connect_axesimage(self, axesimage):
        if globals.debug > 1: print("customcolorbar.connect_axesimage")

        if axesimage in self.axesimages:
            raise Exception("cannot connect AxesImage '"+str(axesimage)+"' to the colorbar because it is already connected")
        self.axesimages.append(axesimage)

        def func(*args,**kwargs):
            self.update_data()
            if self.axiscontroller_connected and self.axis_controller.limits.adaptive.get():
                self.set_adaptive_limits()

        self._axesimages_cids.append(axesimage.get_figure().canvas.mpl_connect("draw_event",func))
        
        #self.update_data()
        #if self.axis_controller.limits.adaptive.get():
        #self.set_adaptive_limits()

    # Called when AxesImage previously connected with connect_axesimage
    # is removed from the plot.
    def disconnect_axesimages(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_axesimage")
        for axesimage, cid in zip(self.axesimages, self._axesimages_cids):
            axesimage.get_figure().canvas.mpl_disconnect(cid)
        self._axesimages_cids = []
        self.axesimages = []

    def disconnect_axesimage(self, axesimage):
        if globals.debug > 1: print("customcolorbar.disconnect_axesimage")
        if axesimage not in self.axesimages:
            raise ValueError("cannot find '"+str(axesimage)+"' in the list of axes images")
        idx = self.axesimages.index(axesimage)
        self.axesimages[idx].get_figure().canvas.mpl_disconnect(self._axesimages_cids[idx])
        self.axesimages.remove(axesimage)
        self._axesimages_cids.remove(self._axesimages_cids[idx])

    def update_position(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_position")
        if not self.connected: return
        pos = self._ax.get_position()

        y0 = pos.y0
        height = pos.height
        
        if self.side == 'right':
            x0 = pos.x1 + self.pad[0]
        elif self.side == 'left':
            x0 = pos.x0 - self.pad[1]
        else:
            raise NotImplementedError("placing the colorbar on the top or bottom of the plot is not yet supported")

        self.cax.set_position([x0,y0,self.width,height])
        self.draw_all()
        self.connected_canvas.draw_idle()
    
    def show(self,side='right'):
        if globals.debug > 1: print("customcolorbar.show")
        # Budge the axis which we are connected to over to the left to
        # accommodate the size of this colorbar

        # Update the position of the axis. This might not be necessary
        #self._ax.get_figure().canvas.draw_idle()
        
        if not self.visible:
            self.side = side
            # Adjust the location of the axis
            pos = self._ax.get_position()
            width = pos.width - self.width
            if self.side == 'right':
                width -= self.pad[0]
                self._ax.set_position([pos.x0,pos.y0,width,pos.height])
                self.cax.set_position([pos.x1 - self.pad[0], pos.y0, self.width, pos.height])
                self.cax.yaxis.tick_right()
                self.cax.yaxis.set_label_position("right")
                self._ax.yaxis.set_label_position("left")
                self._ax.yaxis.tick_left()
            elif self.side == 'left':
                x0 = pos.x0 + 0.5*self.pad[1]
                width -= 0.5*self.pad[1]
                self._ax.set_position([x0,pos.y0,width,pos.height])
                self.cax.set_position([pos.x0, pos.y0, self.width, pos.height])
                self.cax.yaxis.tick_left()
                self.cax.yaxis.set_label_position("left")
                self._ax.yaxis.set_label_position("right")
                self._ax.yaxis.tick_right()
            else:
                raise NotImplementedError("placing the colorbar on the top or bottom of the plot is not yet supported")

        self.visible = True
        self.connect_canvas()
        
    def hide(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.hide")
        
        if self.visible:
            # Adjust the location of the axis
            pos = self._ax.get_position()
            width = pos.width + self.width
            if self.side == 'right':
                width += self.pad[0]
                self._ax.set_position([pos.x0,pos.y0,width,pos.height])
            elif self.side == 'left':
                x0 = pos.x0 - self.pad[1]
                width += self.pad[1]
                self._ax.set_position([x0,pos.y0,width,pos.height])
            else:
                raise NotImplementedError("placing the colorbar on the top or bottom of the plot is not yet supported")
        
        self.visible = False
        self.disconnect_canvas()

    def get_cax_limits(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.get_cax_limits")

        if self.side in ['right', 'left']: return self.cax.get_ylim()
        elif self.side in ['top', 'bottom']: return self.cax.get_xlim()
        else: raise Exception("The colorbar has an unrecognized side attribute",self.side)

    # Updates the colors of the connected AxesImage whenever the
    # limits on the cax are modified. Prevents rapid calls
    def update_axesimage_clim(self,*args,**kwargs):
        if self._after_update_axesimage_clim_cid is not None:
            self.axis_controller.after_cancel(self._after_update_axesimage_clim_cid)
        self._after_update_axesimage_clim_cid = self.axis_controller.after(10, self._update_axesimage_clim)
    
    def _update_axesimage_clim(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.update_axesimage_clim")

        if self.side in ['right', 'left']:
            for image in self.axesimages: image.set_clim(self.cax.get_ylim())
        elif self.side in ['top', 'bottom']:
            for image in self.axesimages: image.set_clim(self.cax.get_xlim())
        else:
            raise Exception("expected one of 'left', 'right', 'top', or 'bottom' for colorbar side but got '"+str(self.side)+"'")

    def set_adaptive_limits(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.set_adaptive_limits")

        data = self.data
        vmin = None
        vmax = None
        for image,d in zip(self.axesimages, data):
            valid = np.isfinite(d)
            if np.any(valid):
                if vmin is None: vmin = np.nanmin(d[valid])
                else: vmin = min(vmin, np.nanmin(d[valid]))
                if vmax is None: vmax = np.nanmax(d[valid])
                else: vmax = max(vmax, np.nanmax(d[valid]))
            image.set_data(d)
        self.axis_controller.limits.low.set(vmin)
        self.axis_controller.limits.high.set(vmax)

    def on_scale_changed(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.on_scale_changed")
        
        # Update the limits
        self.set_adaptive_limits()

        """
        if self.axesimage_connected and self.axiscontroller_connected:
            self.update_data()
            scale = self.axis_controller.scale.get()
            if scale == 'linear': self.axesimage.set_data(self.linear_data)
            elif scale == 'log10':
                print("log10")
                self.axesimage.set_data(np.log10(self.linear_data))
            clim = (np.nanmin(self.axesimage._data), np.nanmax(self.axesimage._data))
            print("setting clim to",clim)
            self.set_clim(clim)
        """

    def update_data(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.update_data")
        if self.axesimage_connected:
            scale = self.axis_controller.scale.get()
            self.linear_data = []
            for i, image in enumerate(self.axesimages):
                data = image.get_array()
                #if isinstance(image, CustomAxesImage): data = image._data
                #elif isinstance(image, matplotlib.image.AxesImage): data = image.get_array()
                #else: raise TypeError("unrecognized image type '"+type(image).__name__+"'")
                
                if scale == 'log10': self.linear_data.append(10**data)
                elif scale == '10^': self.linear_data.append(np.log10(data))
                else: self.linear_data.append(data)

    # Prevent double-calls when both limits change
    def on_axis_controller_limits_changed(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.on_axis_controller_limits_changed")
        if self._after_limits_changed_cid is not None:
            self.axis_controller.after_cancel(self._after_limits_changed_cid)
        self._after_limits_changed_cid = self.axis_controller.after(10, self._on_axis_controller_limits_changed)
    def _on_axis_controller_limits_changed(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar._on_axis_controller_limits_changed")
        if self._after_limits_changed_cid is not None:
            self.axis_controller.after_cancel(self._after_limits_changed_cid)

        vmin, vmax = self.axis_controller.limits.low.get(), self.axis_controller.limits.high.get()

        if self.axesimage_connected:
            for image in self.axesimages: image.set_clim((vmin,vmax))
        
        self.set_clim((vmin, vmax))
    
        
