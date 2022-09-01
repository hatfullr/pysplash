import matplotlib.colorbar
from matplotlib.image import AxesImage
import matplotlib.colors
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
    
    def set_clim(self, cminmax):
        if globals.debug > 1: print("customcolorbar.set_clim")

        axesimage = self.find_axesimage()
        if axesimage is not None:
            if None not in cminmax:
                lim = self.get_cax_limits()
                if any(np.abs((np.array(cminmax)-lim[lim != 0])/lim[lim != 0]) > 0.001):
                    self.vmin = cminmax[0]
                    self.vmax = cminmax[1]
                    self.norm = matplotlib.colors.Normalize(
                        vmin=self.vmin,
                        vmax=self.vmax,
                    )
                    
                    self.draw_all()
    
    def find_axesimage(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.find_axesimage")
        for child in self._ax.get_children():
            if isinstance(child, AxesImage):
                return child
        return None
        
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

    def update_limits(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_limits")
        self.set_clim(self.calculate_limits())

    def connect_canvas(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.connect_canvas")
        self.connected_canvas = self._ax.get_figure().canvas
        self.connect_resize()
        self.connect_draw()

    def disconnect_canvas(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_canvas")
        self.disconnect_resize()
        self.disconnect_draw()
        self.connected_canvas = None

    def connect_resize(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.connect_resize")
        self.show_cid = self.connected_canvas.mpl_connect("resize_event",self.update_position)
    def disconnect_resize(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_resize")
        if self.show_cid is not None:
            self.connected_canvas.mpl_disconnect(self.show_cid)
        self.show_cid = None

    def connect_axesimage(self, axesimage):
        if globals.debug > 1: print("customcolorbar.connect_axesimage")
        
        if self.side in ['right', 'left']:
            self.image_cid = self.cax.callbacks.connect(
                "ylim_changed",
                lambda *args, **kwargs: axesimage.set_clim(self.cax.get_ylim())
            )
        elif seld.side in ['top', 'bottom']:
            self.image_cid = self.cax.callbacks.connect(
                "xlim_changed",
                lambda *args, **kwargs: axesimage.set_clim(self.cax.get_xlim())
            )
        else: raise ValueError("Colorbar has an invalid side '",self.side,"'")
        
    def disconnect_axesimage(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_axesimage")
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
        
    def update_position(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_position")
        
        fig = self._ax.get_figure()
        fig.canvas.draw_idle() # Need to update the figure to get the right position
        pos = self._ax.get_position()
        right = fig.subplotpars.right
        left = fig.subplotpars.left

        aspect = pos.height/pos.width
        
        if pos == self.previous_ax_position: return
        self.previous_ax_position = pos
        
        if self.side == 'right':
            d = self.width + sum(self.pad)
            
            new_ax_x0 = pos.x0
            new_ax_x1 = right - d

            changey = (pos.width - (new_ax_x1-new_ax_x0)) * aspect
            
            new_ax_y0 = pos.y0 + 0.5*changey
            new_ax_y1 = pos.y1 - 0.5*changey
            
            x0 = new_ax_x1 + self.pad[0]
            y0 = new_ax_y0
            height = new_ax_y1 - new_ax_y0
            
            self.cax.yaxis.tick_right()

            # Budge the axis to the left
            self._ax.set_position([
                new_ax_x0,
                new_ax_y0,
                new_ax_x1-new_ax_x0,
                new_ax_y1-new_ax_y0,
            ])
            
        elif self.side == 'left':
            d = self.width + sum(self.pad)
            
            new_ax_x0 = left + d
            new_ax_x1 = pos.x1

            changey = (pos.width - (new_ax_x1-new_ax_x0)) * aspect
            
            new_ax_y0 = pos.y0 + 0.5*changey
            new_ax_y1 = pos.y1 - 0.5*changey
            
            x0 = new_ax_x0 - (self.width + self.pad[0])
            y0 = new_ax_y0
            height = new_ax_y1 - new_ax_y0
            
            self.cax.yaxis.tick_left()

            # Budge the axis to the left
            self._ax.set_position([
                new_ax_x0,
                new_ax_y0,
                new_ax_x1-new_ax_x0,
                new_ax_y1-new_ax_y0,
            ])

        elif self.side == 'top' or self.side == 'bottom':
            raise ValueError("Placing the colorbar on the top or bottom of the plot is not yet supported")
        
        self.cax.set_position([x0,y0,self.width,height])
        self.draw_all()
        
    def show(self,side='right'):
        if globals.debug > 1: print("customcolorbar.show")

        if not self.visible:
            self.update_position()
            self.visible = True
            self.connect_canvas()

            self._ax.get_figure().canvas.draw_idle()

    def hide(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.hide")

        if self.previous_ax_position is None:
            # Colorbar has yet to be shown
            return

        if self.visible:
        
            # Hide the colorbar
            self.visible = False

            self.disconnect_canvas()
        
            # Put the axis back where it was originally
            self._ax.set_position(self.previous_ax_position)
            self._ax.get_figure().draw_idle()
        
    @property
    def visible(self):
        return self.cax.get_visible()

    @visible.setter
    def visible(self, value):
        self.cax.set_visible(value)

    def get_cax_limits(self, *args, **kwargs):
        if globals.debug > 1: print("customcolorbar.get_cax_limits")

        if self.side in ['right', 'left']: return self.cax.get_ylim()
        elif self.side in ['top', 'bottom']: return self.cax.get_xlim()
        else: raise Exception("The colorbar has an unrecognized side attribute",self.side)
