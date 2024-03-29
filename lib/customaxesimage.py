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
    def __init__(self,ax,data,aspect=None,initialize=True,extent=None,interpolation='nearest',colorbar=None,xunits=1.,yunits=1.,aftercalculate=None,resolution_steps=(0.01, 0.1, 0.5, 1),**kwargs):
        if globals.debug > 1: print("customaxesimage.__init__")
        self.ax = ax
        self.fig = self.ax.get_figure()
        self.widget = self.fig.canvas.get_tk_widget()
        #self.cscale = cscale
        self.xunits = xunits
        self.yunits = yunits
        self.aspect = aspect
        self.aftercalculate = aftercalculate
        self.resolution_steps = resolution_steps

        self.resolution_step = 0
        self._interrupt = False

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
            extent = list(self.ax.get_xlim())+list(self.ax.get_ylim())

        kwargs['origin'] = 'lower'
        self.kwargs = kwargs

        super(CustomAxesImage, self).__init__(self.ax,extent=extent,interpolation=interpolation,**kwargs)
        self._extent = extent

        if self.data_is_image:
            super(CustomAxesImage,self).set_data(self._data)
        else:
            super(CustomAxesImage,self).set_data([[],[]])
        self.ax.add_image(self)

        self.colorbar = colorbar
        if self.colorbar is not None:
            self.colorbar.connect_axesimage(self)

        self.calculating = False

        if not self.data_is_image:
            self.previous_xlim = self.ax.get_xlim()
            self.previous_ylim = self.ax.get_ylim()
        
            self.thread = None

            self.threaded = True
            if initialize:
                self.widget.after(1, self._calculate)
                #self._calculate()

    def __str__(self,*args,**kwargs): return "CustomAxesImage(%g,%g;%gx%g)" % tuple(self.ax.bbox.bounds)

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
        self.cancel() # Cancel any running calculations
        if self.colorbar is not None:
            self.colorbar.disconnect_axesimage(self)
        super(CustomAxesImage,self).remove(*args,**kwargs)
    
    def equalize_aspect_ratio(self,xlim=None,ylim=None):
        if globals.debug > 1: print("customaxesimage.equalize_aspect_ratio")
        flag = False
        if xlim is None and ylim is None: flag = True
        
        if flag:
            #self._disconnect()
            xlim,ylim = self.ax.get_xlim(),self.ax.get_ylim()
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
            #self.ax.set_xlim(xlim)
            #self.ax.set_ylim(ylim)
            #self._connect()
            pass
        else:
            return xlim, ylim
    
    
    def calculate_xypixels(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.calculate_xypixels")
        self.dpi = self.fig.dpi
        bbox = self.ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        self.xpixels = int(bbox.width*self.dpi * self.resolution_step)
        self.ypixels = int(bbox.height*self.dpi * self.resolution_step)
        
    def _calculate(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage._calculate")

        self.calculating = True

        for self.resolution_step in self.resolution_steps:
            if self._interrupt:
                self.cancel()
                return
            self.calculate_xypixels()

            #print(self.xpixels, self.ypixels)

            if self.aspect == 'equal': self.equalize_aspect_ratio()
            if not (self.ypixels == self._data.shape[0] and self.xpixels == self._data.shape[1]):
                self._data = np.resize(self._data,(self.ypixels,self.xpixels)) # Fills new entries with 0

            if self.threaded:
                while self.thread is not None:
                    self.widget.update()
                    if self._interrupt:
                        self.cancel()
                        return

                self.thread = ThreadedTask(
                    self.widget,
                    target=self.calculate,
                    args=args,
                    kwargs=kwargs,
                    callback=self._after_calculate,
                )
                
            else:
                self.calculate(*args,**kwargs)
                self._after_calculate()


        # Block until the previous thread has finished
        while self.thread is not None:
            self.widget.update()
            if self._interrupt:
                self.cancel()
                return
        #self.calculating = False
        #if self.aftercalculate is not None:
        #    self.aftercalculate()
        

    def _after_calculate(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage._after_calculate")
        self.thread = None
        self.set_data(self._data)
        
        self.after_calculate()
        if self.aftercalculate is not None:
            self.aftercalculate(*args,**kwargs)

        if self.resolution_step == self.resolution_steps[-1]:
            self.calculating = False
    
    def set_data(self,new_data):
        if globals.debug > 1: print("customaxesimage.set_data")
        self._data = new_data
        super(CustomAxesImage,self).set_data(new_data)

    def cancel(self,*args,**kwargs):
        if globals.debug > 1: print("customaxesimage.cancel")
        self._interrupt = True
        self.calculating = False
        if self.thread is not None: self.thread.stop()
