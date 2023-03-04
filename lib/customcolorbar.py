import matplotlib.colorbar
from matplotlib.image import AxesImage
from widgets.axiscontroller import AxisController
import matplotlib.colors
import matplotlib.image
import matplotlib
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
            self.vmin = min(cminmax)
            self.vmax = max(cminmax)
            self.norm = matplotlib.colors.Normalize(vmin=self.vmin,vmax=self.vmax)

            if self.axiscontroller_connected:
                scale = self.axis_controller.scale.get()
                if scale == 'log10': self.vmin = max(self.vmin, AxisController.min_log_default)

            if np.isnan(self.vmin): self.vmin = 0 # Fallback in emergency
            if np.isnan(self.vmax): self.vmax = 1 # Fallback in emergency

            # Implicitly calls update_axesimage_clim when cax limits are modified
            if self.vmax != self.vmin:
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

        def func(*args,**kwargs):
            if self.axiscontroller_connected and self.axis_controller.limits.adaptive.get():
                self.set_adaptive_limits()

        self.axesimages.append(axesimage)
        self._axesimages_cids.append(axesimage.get_figure().canvas.mpl_connect("draw_event",func))
        
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
        if axesimage in self.axesimages:
            idx = self.axesimages.index(axesimage)
            fig = self.axesimages[idx].get_figure()
            if fig is not None:
                fig.canvas.mpl_disconnect(self._axesimages_cids[idx])
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

    def get_cax_limits(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.get_cax_limits")

        if self.side in ['right', 'left']: return self.cax.get_ylim()
        elif self.side in ['top', 'bottom']: return self.cax.get_xlim()
        else: raise Exception("The colorbar has an unrecognized side attribute",self.side)

    def update_axesimage_clim(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.update_axesimage_clim")

        if self.axesimage_connected:
            # Before drawing the new plot to the screen, update the colors to
            # omit "bad" colors (NaN and Inf)
            scale = self.axis_controller.scale.get()
            
            vmin, vmax = self.vmin, self.vmax
            if scale == 'log10':
                vmin, vmax = 10**vmin, 10**vmax
                for image in self.axesimages:
                    data = np.array(image.get_array()) # Removes any masking
                    data[~np.isfinite(np.log10(data))] = np.nan
                    image.set_data(data)
            elif scale == '10^':
                vmin, vmax = np.log10(max(vmin, AxisController.min_log_default)), np.log10(vmax)

            if scale != 'log10':
                for image in self.axesimages:
                    data = np.array(image.get_array())
                    data[~np.isfinite(data)] = 0
                    image.set_data(data)
            
            for image in self.axesimages:
                image.set_clim(vmin,vmax)

    def update_bad_values(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.update_bad_values")
        scale = self.axis_controller.scale.get()
        if scale == 'log10':
            for image in self.axesimages:
                data = np.array(image.get_array()) # Removes any masking
                data[~np.isfinite(np.log10(data))] = np.nan
                image.set_data(data)
        else:
            for image in self.axesimages:
                data = np.array(image.get_array())
                data[~np.isfinite(data)] = 0
                image.set_data(data)

    def set_adaptive_limits(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.set_adaptive_limits")

        if self.axesimage_connected:
            scale = self.axis_controller.scale.get()
            
            vmin = None
            vmax = None
            for image in self.axesimages:
                d = image.get_array()
                valid = np.isfinite(d)
                if np.any(valid):
                    if vmin is None: vmin = np.nanmin(d[valid])
                    else: vmin = min(vmin, np.nanmin(d[valid]))
                    if vmax is None: vmax = np.nanmax(d[valid])
                    else: vmax = max(vmax, np.nanmax(d[valid]))

            if scale == 'log10':
                if vmin is not None: vmin = np.log10(max(vmin, AxisController.min_log_default))
                if vmax is not None: vmax = np.log10(vmax)
            elif scale == '10^':
                if vmin is not None: vmin = 10**vmin
                if vmax is not None: vmax = 10**vmax

            if vmin is not None:
                self.axis_controller.limits.low.set(vmin)
            if vmax is not None:
                self.axis_controller.limits.high.set(vmax)

    def on_scale_changed(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.on_scale_changed")
        
        # Update the limits
        self.set_adaptive_limits()

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
        self.set_clim((vmin, vmax))

    def update_cmap(self, new_cmap):
        if globals.debug > 1: print('customcolorbar.update_cmap')
        self.cmap = matplotlib.pyplot.get_cmap(new_cmap)
        for image in self.axesimages:
            image.set_cmap(new_cmap)
        self.draw_all()
        self.cax.get_figure().canvas.draw_idle()
