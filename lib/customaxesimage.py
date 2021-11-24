from sys import version_info
if version_info.major < 3:
    from threadedtask import ThreadedTask
else:
    from lib.threadedtask import ThreadedTask
import matplotlib.image
import numpy as np
from copy import copy
import globals

class CustomAxesImage(matplotlib.image.AxesImage,object):
    def __init__(self,ax,data,xscale='linear',yscale='linear',cscale='linear',aspect=None,**kwargs):
        if globals.debug > 1: print("customaxesimage.__init__")
        self._axes = ax
        self.widget = self._axes.get_figure().canvas.get_tk_widget()
        self.xscale = xscale
        self.yscale = yscale
        self.cscale = cscale
        self.aspect = aspect
        
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
        if globals.debug > 1: print("customaxesimage.after")
        return self.widget.after(*args,**kwargs)
    def after_cancel(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.after_cancel")
        self.widget.after_cancel(*args,**kwargs)

    def _connect(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage._connect")
        self.cids = [
            self._axes.callbacks.connect('xlim_changed',self.wait_to_calculate),
            self._axes.callbacks.connect('ylim_changed',self.wait_to_calculate),
            self._axes.get_figure().callbacks.connect('dpi_changed',self.calculate_xypixels),
            self._axes.callbacks.connect('resize_event',self.calculate_xypixels),
        ]
    def _disconnect(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage._disconnect")
        for cid in self.cids:
            for obj in [self._axes,self._axes.get_figure()]:
                obj.callbacks.disconnect(cid)

    def remove(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.remove")
        # Make sure we disconnect any connections we made to the associated axes
        # before removing the image
        self._disconnect()
        super(CustomAxesImage,self).remove(*args,**kwargs)
                
    def equalize_aspect_ratio(self,xlim=None,ylim=None):
        if globals.debug > 1: print("customaxesimage.equalize_aspect_ratio")
        flag = False
        if xlim is None and ylim is None: flag = True
        
        if flag:
            self._disconnect()
            xlim,ylim = self._axes.get_xlim(),self._axes.get_ylim()
        dx = xlim[1]-xlim[0]
        dy = ylim[1]-ylim[0]
        cx = 0.5*(xlim[1]+xlim[0])
        cy = 0.5*(ylim[1]+ylim[0])
        if dx < dy:
            xlim = [cx-0.5*dy,cx+0.5*dy]
        else:
            ylim = [cy-0.5*dx,cy+0.5*dx]
        if flag:
            self._axes.set_xlim(xlim)
            self._axes.set_ylim(ylim)
            self._connect()
            self._axes.get_figure().canvas.draw_idle()
        else:
            return xlim, ylim
        
    def calculate_xypixels(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.calculate_xypixels")
        fig = self._axes.get_figure()
        self.dpi = fig.dpi
        bbox = self._axes.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        self.xpixels = int(bbox.width*self.dpi)
        self.ypixels = int(bbox.height*self.dpi)
        
    def _calculate(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage._calculate")
        self.after_id_calculate = None
        if self.aspect == 'equal': self.equalize_aspect_ratio()
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
        if globals.debug > 1: print("customaxesimage._after_calculate")
        self.thread = None
        self._unscaled_data = copy(self._data)
        self.set_data(self._data)
        self.after_calculate()
        self._axes.get_figure().canvas.draw_idle()

    # Allow a calculation to happen only once every 10 miliseconds
    # Prevents double calculation when both x and y limits change
    def wait_to_calculate(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.wait_to_calculate")
        if self.after_id_calculate is not None:
            self.after_cancel(self.after_id_calculate)
        self.after_id_calculate = self.after(10,lambda args=args,kwargs=kwargs:self._calculate(*args,**kwargs))

    def set_data(self,new_data,scaled=True):
        if globals.debug > 1: print("customaxesimage.set_data")
        #self._data = new_data
        if scaled:
            if new_data.dtype != 'bool':
                if self.cscale == 'log10': new_data = np.log10(new_data)
                elif self.cscale == '^10': new_data = 10.**new_data
        self._data = new_data
        super(CustomAxesImage,self).set_data(new_data)
        self._axes.get_figure().canvas.get_tk_widget().event_generate("<<DataChanged>>")

    def update_cscale(self,cscale):
        if globals.debug > 1: print("customaxesimage.update_cscale")
        if cscale != self.cscale:
            if cscale == 'linear': data = self._unscaled_data
            elif cscale == 'log10': data = np.log10(self._unscaled_data)
            elif cscale == '^10': data = 10.**self._unscaled_data
            self.cscale = cscale
            self.set_data(data,scaled=False)

