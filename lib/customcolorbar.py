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
        
        self._ax.get_figure().canvas.mpl_connect('draw_event',self.update_limits)
        self.show_cid = None
        self.connected_canvas = None

    def update_limits(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_limits")

        # Get the color data in the plot
        for child in self._ax.get_children():
            if isinstance(child, AxesImage):
                data = child._data
                vmin = np.nanmin(data[np.isfinite(data)])
                vmax = np.nanmax(data[np.isfinite(data)])
                self.norm = matplotlib.colors.Normalize(
                    vmin=vmin,
                    vmax=vmax,
                )
                child.set_clim(vmin,vmax)
                self.draw_all()
                return

    def connect_show(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.connect_show")
        self.connected_canvas = self._ax.get_figure().canvas
        self.show_cid = self.connected_canvas.mpl_connect("resize_event",self.update_position)
    def disconnect_show(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.disconnect_show")
        if self.show_cid is not None:
            self.connected_canvas.mpl_disconnect(self.show_cid)
            self.show_cid = None
            self.connected_canvas = None


    def update_position(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.update_position")
        
        pos = self._ax.get_position()

        fig = self._ax.get_figure()
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

        if not self.cax.get_visible():
        
            self.update_position()
            self.cax.set_visible(True)
            self.connect_show()
        
            self._ax.get_figure().canvas.draw_idle()
        

    def hide(self,*args,**kwargs):
        if globals.debug > 1: print("customcolorbar.hide")

        if self.previous_ax_position is None:
            # Colorbar has yet to be shown
            return

        if self.cax.get_visible():
        
            # Hide the colorbar
            self.cax.set_visible(False)

            self.disconnect_show()
        
            # Put the axis back where it was originally
            self._ax.set_position(self.previous_ax_position)

            self._ax.get_figure().canvas.draw_idle()
        
        
        