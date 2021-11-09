from sys import version_info
if version_info.major < 3:
    from threadedtask import ThreadedTask
else:
    from lib.threadedtask import ThreadedTask
import matplotlib.image
import numpy as np
from copy import copy

class CustomAxesImage(matplotlib.image.AxesImage,object):
    def __init__(self,ax,data,scale='linear',physical_units=None,display_units=None,**kwargs):
        self._axes = ax
        self.widget = self._axes.get_figure().canvas.get_tk_widget()
        self.scale = scale
        self.display_units = display_units
        self.physical_units = physical_units

        if ((self.display_units is not None and self.physical_units is None) or
            (self.display_units is None and self.physical_units is not None)):
            raise ValueError("Cannot have only one of physical_units and display_units be None")
        
        self._data = copy(data)
        self.calculate_xypixels()
        
        kwargs['extent'] = list(self._axes.get_xlim())+list(self._axes.get_ylim())
        kwargs['origin'] = 'lower'
        matplotlib.image.AxesImage.__init__(self,self._axes,**kwargs)
        self._axes.add_image(self)
        self.threaded = False

        self.thread = None
        
        self._extent = kwargs['extent']

        self._connect()

        self.after_id_calculate = None
        
        self._calculate()
        self.threaded = True

    def calculate(self,*args,**kwargs):
        # To be created by a child class
        pass
    def after_calculate(self,*args,**kwargs):
        # To be created by a child class
        pass
        
    def after(self,*args,**kwargs):
        return self.widget.after(*args,**kwargs)
    def after_cancel(self,*args,**kwargs):
        self.widget.after_cancel(*args,**kwargs)

    def _connect(self,*args,**kwargs):
        self.cids = [
            self._axes.callbacks.connect('xlim_changed',self.wait_to_calculate),
            self._axes.callbacks.connect('ylim_changed',self.wait_to_calculate),
            self._axes.get_figure().callbacks.connect('dpi_changed',self.calculate_xypixels),
            self._axes.callbacks.connect('resize_event',self.calculate_xypixels),
        ]
    def _disconnect(self,*args,**kwargs):
        for cid in self.cids:
            for obj in [self._axes,self._axes.get_figure()]:
                obj.callbacks.disconnect(cid)

    def remove(self,*args,**kwargs):
        # Make sure we disconnect any connections we made to the associated axes
        # before removing the image
        self._disconnect()
        super(CustomAxesImage,self).remove(*args,**kwargs)
                
    def equalize_aspect_ratio(self,*args,**kwargs):
        self._disconnect()
        xlim,ylim = self._axes.get_xlim(),self._axes.get_ylim()
        dx = xlim[1]-xlim[0]
        dy = ylim[1]-ylim[0]
        cx = 0.5*(xlim[1]+xlim[0])
        cy = 0.5*(ylim[1]+ylim[0])
        if dx < dy:
            self._axes.set_xlim(cx-0.5*dy,cx+0.5*dy)
        else:
            self._axes.set_ylim(cy-0.5*dx,cy+0.5*dx)
        self._connect()
        self._axes.get_figure().canvas.draw_idle()
        
    def calculate_xypixels(self,*args,**kwargs):
        fig = self._axes.get_figure()
        self.dpi = fig.dpi
        bbox = self._axes.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        self.xpixels = int(bbox.width*self.dpi)
        self.ypixels = int(bbox.height*self.dpi)
        
    def _calculate(self,*args,**kwargs):
        self.after_id_calculate = None
        self.equalize_aspect_ratio()
        if not (self.ypixels == self._data.shape[0] and self.xpixels == self._data.shape[1]):
            self._data = np.resize(self._data,(self.ypixels,self.xpixels)) # Fills new entries with 0
        if self.threaded:
            if self.thread is not None:
                self.wait_to_calculate(*args,**kwargs)
                return

            self.thread = ThreadedTask(
                self._axes.get_figure().canvas.get_tk_widget(),
                target=self.calculate,
                args=args,
                kwargs=kwargs,
                callback=self._after_calculate,
            )
        else:
            self.calculate(*args,**kwargs)
            self._after_calculate()

    def _after_calculate(self,*args,**kwargs):
        self.thread = None
        if self.display_units is not None and self.physical_units is not None:
            self._extent = [
                self._extent[0]*self.display_units[0],
                self._extent[1]*self.display_units[0],
                self._extent[2]*self.display_units[1],
                self._extent[3]*self.display_units[1],
            ]
        if self.scale == 'log10': self._data = np.log10(self._data)
        elif self.scale == '^10': self._data = 10**self._data
        self.set_data(self._data)
        self.after_calculate()
        self._axes.get_figure().canvas.draw_idle()

    # Allow a calculation to happen only once every 10 miliseconds
    # Prevents double calculation when both x and y limits change
    def wait_to_calculate(self,*args,**kwargs):
        if self.after_id_calculate is not None:
            self.after_cancel(self.after_id_calculate)
        self.after_id_calculate = self.after(10,lambda args=args,kwargs=kwargs:self._calculate(*args,**kwargs))

    def set_data(self,new_data):
        self._data = new_data
        if (self._data.dtype != 'bool' and
            self.physical_units is not None and
            self.display_units is not None):
            self._data *= self.display_units[2] / (self.display_units[0]*self.display_units[1])
            
        super(CustomAxesImage,self).set_data(new_data)
        self._axes.get_figure().canvas.get_tk_widget().event_generate("<<DataChanged>>")
        
    def get_scale(self):
        return self.scale
        
    def set_scale(self,scale):
        if scale != self.scale:
            if self.scale == 'linear':
                if scale == 'log10':
                    self.set_data(np.log10(self._data))
                elif scale == '^10':
                    self.set_data(10**self._data)
            elif self.scale == 'log10':
                if scale == 'linear':
                    self.set_data(10**self._data)
                elif scale == '^10':
                    self.set_data(10**(10**self._data))
            elif self.scale == '^10':
                if scale == 'linear':
                    self.set_data(np.log10(self._data))
                elif scale == 'log10':
                    self.set_data(np.log10(np.log10(self._data)))
            self.scale = scale
            self._axes.get_figure().canvas.draw_idle()
