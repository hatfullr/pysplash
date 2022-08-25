from sys import version_info
if version_info.major < 3:
    from threadedtask import ThreadedTask
else:
    from lib.threadedtask import ThreadedTask
import matplotlib.image
import numpy as np
from copy import copy
import globals
from collections import OrderedDict
from lib.customcolorbar import CustomColorbar

# interpolation 'nearest' is significantly faster than interpolation 'none'
class CustomAxesImage(matplotlib.image.AxesImage,object):
    def __init__(self,ax,data,cscale='linear',aspect=None,initialize=True,extent=None,interpolation='nearest',colorbar=None,cunits=1.,xunits=1.,yunits=1.,aftercalculate=None,**kwargs):
        if globals.debug > 1: print("customaxesimage.__init__")
        self._axes = ax
        self.widget = self._axes.get_figure().canvas.get_tk_widget()
        self.cscale = cscale
        self.xunits = xunits
        self.yunits = yunits
        self.cunits = cunits
        self.aspect = aspect
        self.aftercalculate = aftercalculate

        self.calculating = False
        
        self.data_is_image = False
        if hasattr(data,"is_image"):
            if data.is_image:
                self.data_is_image = True
                if 'extent' not in data.keys() or 'image' not in data.keys():
                    raise ValueError("Your OrderedDict is missing the keyword 'extent'")
            self._data = copy(data['image'])
            extent = data['extent']
        else:
            self._data = copy(data)            
            extent = list(self._axes.get_xlim())+list(self._axes.get_ylim())

        kwargs['origin'] = 'lower'

        super(CustomAxesImage, self).__init__(self._axes,extent=extent,interpolation=interpolation,**kwargs)
        self._extent = extent

        if self.data_is_image:
            super(CustomAxesImage,self).set_data(self._data)
        else:
            super(CustomAxesImage,self).set_data([[],[]])
        self._axes.add_image(self)

        self.colorbar = colorbar
        if self.colorbar is not None:
            self.colorbar.connect_axesimage(self)

        if not self.data_is_image:
            self.previous_xlim = self._axes.get_xlim()
            self.previous_ylim = self._axes.get_ylim()
        
            self.thread = None
            #self._connect()

            self.after_id_calculate = None
        
            self.threaded = True
            if initialize: self._calculate()

    def calculate(self,*args,**kwargs):
        # To be created by a child class
        pass
    def after_calculate(self,*args,**kwargs):
        # To be created by a child class
        pass

    def remove(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.remove")
        # Make sure we disconnect any connections we made to the associated axes
        # before removing the image
        if self.after_id_calculate is not None: self.widget.after_cancel(self.after_id_calculate)
        
        if self.colorbar is not None: self.colorbar.disconnect_axesimage()
        super(CustomAxesImage,self).remove(*args,**kwargs)
    
    def equalize_aspect_ratio(self,xlim=None,ylim=None):
        if globals.debug > 1: print("customaxesimage.equalize_aspect_ratio")
        flag = False
        if xlim is None and ylim is None: flag = True
        
        if flag:
            #self._disconnect()
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
            # I don't know why, but these lines break everything.
            #self._axes.set_xlim(xlim)
            #self._axes.set_ylim(ylim)
            #self._connect()
            pass
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
        self.calculating = True
        self.calculate_xypixels()
        
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
        self.set_data(self._data)
        
        # Update this image's colors based on the colorbar's limits
        if self.colorbar is not None:
            self.set_clim(self.colorbar.get_cax_limits())
        
        self.after_id_calculate = None
        self.calculating = False
        self.after_calculate()
        if self.aftercalculate is not None: self.aftercalculate(*args,**kwargs)
    
    # Allow a calculation to happen only once every 10 miliseconds
    # Prevents double calculation when both x and y limits change
    def wait_to_calculate(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.wait_to_calculate")
        #print(self,"wait to calculate",self.after_id_calculate, args,kwargs)
        if self.after_id_calculate is None:
            self.after_id_calculate = self.widget.after(10,lambda args=args,kwargs=kwargs:self._calculate(*args,**kwargs))
        else:
            self.widget.after_cancel(self.after_id_calculate)
            self.after_id_calculate = None

    def set_data(self,new_data,raw=False):
        if globals.debug > 1: print("customaxesimage.set_data")
        if not raw:
            if new_data.dtype != 'bool':
                if self.cscale == 'log10': new_data = np.log10(new_data)
                elif self.cscale == '^10': new_data = 10.**new_data
        self._data = new_data.astype('uint8')
        super(CustomAxesImage,self).set_data(new_data)

