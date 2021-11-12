import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from customaxesimage import CustomAxesImage
    #from threadedtask import ThreadedTask
else:
    import tkinter as tk
    from lib.customaxesimage import CustomAxesImage
    #from lib.threadedtask import ThreadedTask

import globals
if globals.debug > 0: from time import time
import numpy as np
import math

try:
    from numba import cuda,float64
    import math
    has_jit = True
except ImportError:
    has_jit = False

class ScatterPlot(CustomAxesImage,object):
    # s is size of markers in points**2
    def __init__(self,ax,x,y,s=1,**kwargs):
        if globals.debug > 1: print("scatterplot.__init__")
        self.ax = ax
        self.x = x
        self.y = y
        self.s = s

        self.previous_x = None
        self.previous_y = None
        
        self.initializing = True
        self.set_size(s)
        
        kwargs['cmap'] = 'binary'
        super(ScatterPlot,self).__init__(
            self.ax,
            np.full((1,1),False,dtype='bool'),
            **kwargs
        )
        
        self.initializing = False

    def set_size(self,size):
        if globals.debug > 1: print("scatterplot.set_size")
        if isinstance(size,tk.IntVar):
            try:
                size = int(size.get())
            except Exception as e:
                # If the variable is empty, do nothing
                if (str(e) == 'expected floating-point number but got ""' or
                    str(e) == 'expected integer but got ""' or
                    "invalid literal for int() with base 10: " in str(e)):
                    return
                else: raise
        if size <= 0:
            return # Do nothing if invalid pixel size
        if size != self.s:
            self.s = size
            if not self.initializing:
                self.calculate_xypixels()
                self._calculate()
    
    def calculate_xypixels(self,*args,**kwargs):
        if globals.debug > 1: print("scatterplot.calculate_xypixels")
        fig = self.ax.get_figure()
        self.dpi = fig.dpi
        bbox = self.ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        self.xpixels = int(bbox.width*self.dpi / self.s)
        self.ypixels = int(bbox.height*self.dpi / self.s)
        
        # On my machine, I expect about 1326 pixels wide and 1318 pixels tall
        # Got 1329x1321 pixels, which I think makes sense because the thickness
        # of the axis spines is 3 pixels.
        if globals.debug > 1:
            print("   xpixels,ypixels =",self.xpixels,self.ypixels)
    
    def calculate(self,*args,**kwargs):
        if globals.debug > 1: print("scatterplot.calculate")
        if globals.debug > 0: start = time()
        xmin,xmax,ymin,ymax = list(self.ax.get_xlim())+list(self.ax.get_ylim())
        idx = np.logical_and(
            np.logical_and(self.x > xmin, self.x < xmax),
            np.logical_and(self.y > ymin, self.y < ymax),
        )
        if any(idx):
            self._extent = [xmin,xmax,ymin,ymax]
            self.dx = (xmax-xmin)/float(self.xpixels)
            self.dy = (ymax-ymin)/float(self.ypixels)
            
            self._data[:] = False
            self.calculate_data(self.x[idx],self.y[idx])
            if globals.debug > 0: print("scatterplot.calculate took %f seconds" % (time()-start))

    if has_jit:
        @staticmethod
        @cuda.jit
        def calculate_indices(data,delta_xy,invdx,invdy):
            i = cuda.grid(1)
            if i < delta_xy.size:
                data[int(delta_xy[i][1]*invdy),int(delta_xy[i][0]*invdx)] = True

        def calculate_data_gpu(self,x,y):
            if globals.debug > 1: print("scatterplot.calculate_data_gpu")
            threadsperblock=512
            N = len(x)
            # Center on each pixel, so -0.5*dx and -0.5*dy
            delta_xy = np.column_stack((x,y))-np.array([self._extent[0]-0.5*self.dx,self._extent[2]-0.5*self.dy])
            device_delta_xy = cuda.to_device(delta_xy)

            device_data = cuda.to_device(self._data)

            blockspergrid = N // threadsperblock + 1
            
            self.calculate_indices[blockspergrid,threadsperblock](
                device_data,
                device_delta_xy,
                1./self.dx,
                1./self.dy,
            )
            cuda.synchronize()
            self._data = device_data.copy_to_host()
            
    else:
        def calculate_data_gpu(self,*args,**kwargs):
            return self.calculate_data_cpu(*args,**kwargs)

    def calculate_data_cpu(self,x,y):
        if globals.debug > 1: print("scatterplot.calculate_data_cpu")
        xmin,xmax,ymin,ymax = self._extent
        for xp,yp in zip(x,y):
            self._data[int((yp-ymin)/self.dy),int((xp-xmin)/self.dx)] = True
    
    def calculate_data(self,x,y):
        if globals.debug > 1: print("scatterplot.calculate_data")
        try:
            self.calculate_data_gpu(x,y)
        except:
            self.calculate_data_cpu(x,y)

