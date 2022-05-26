import sys
if sys.version_info.major < 3:
    import Tkinter as tk
    from customaxesimage import CustomAxesImage
else:
    import tkinter as tk
    from lib.customaxesimage import CustomAxesImage

import globals
from time import time
import numpy as np
import math
import multiprocessing

try:
    from numba import cuda
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

        self.cpu_mp_time = 0.
        self.cpu_serial_time = np.inf
        
        kwargs['cmap'] = 'binary'
        super(ScatterPlot,self).__init__(
            self.ax,
            np.full((1,1),False,dtype='bool'),
            **kwargs
        )

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
            self._extent = np.array([xmin,xmax,ymin,ymax])
            self.dx = (xmax-xmin)/float(self.xpixels)
            self.dy = (ymax-ymin)/float(self.ypixels)
            
            self._data[:] = False
            if has_jit:
                self.calculate_data_gpu(self.x[idx],self.y[idx])
            else:
                self.calculate_data_cpu(self.x[idx],self.y[idx])
            
            if globals.debug > 0: print("scatterplot.calculate took %f seconds" % (time()-start))

    if has_jit:
        @staticmethod
        @cuda.jit
        def calculate_indices_gpu(data,delta_xy,invdx,invdy):
            i = cuda.grid(1)
            if i < delta_xy.shape[0]:
                data[int(delta_xy[i][1]*invdy),int(delta_xy[i][0]*invdx)] = True

        def calculate_data_gpu(self,x,y):
            if globals.debug > 1: print("scatterplot.calculate_data_gpu")
            threadsperblock=512
            N = len(x)
            # Center on each pixel, so -0.5*dx and -0.5*dy
            delta_xy = np.column_stack((x,y))-np.array([self._extent[0]-0.5*self.dx,self._extent[2]-0.5*self.dy])
            try:
                device_delta_xy = cuda.to_device(delta_xy)
                device_data = cuda.to_device(self._data)
            except Exception as e:
                print("Unexpected error encountered while copying data from the host to the gpu")
                print(e)
                cuda.get_current_device().reset()
                return

            blockspergrid = N // threadsperblock + 1
            
            self.calculate_indices_gpu[blockspergrid,threadsperblock](
                device_data,
                device_delta_xy,
                1./self.dx,
                1./self.dy,
            )
            try:
                cuda.synchronize()
            except Exception as e:
                print("Unexpected error encountered while copying data from the gpu to the host")
                print(e)
                cuda.get_current_device().reset()
                return
            self._data = device_data.copy_to_host()

    def calculate_data_cpu(self,x,y):
        if globals.debug > 1: print("scatterplot.calculate_data_cpu")
        if globals.use_multiprocessing_on_scatter_plots:
            self.calculate_data_cpu_mp(x,y)
        else:
            self.calculate_data_cpu_serial(x,y)
            
    def calculate_data_cpu_serial(self,x,y,data=None):
        if globals.debug > 1: print("scatterplot.calculate_data_cpu_serial")
        # This is the fastest I could possibly make it
        if data is None: data = self._data
        indices_x = ((x-self._extent[0])/self.dx-0.5).astype(int,copy=False)
        indices_y = ((y-self._extent[2])/self.dy-0.5).astype(int,copy=False)
        data[indices_y,indices_x] = True
        

    def calculate_data_cpu_mp(self,x,y,data=None):
        if globals.debug > 1: print("scatterplot.calculate_data_mp")
        if data is None: data = self._data
        pool = multiprocessing.Pool()
        nprocs = pool._processes

        chunks = np.array_split(np.arange(len(x)),nprocs)
        
        procs = [None]*nprocs
        for p in range(nprocs):
            chunk = chunks[p]
            procs[p] = pool.apply_async(
                calculate_indices_cpu,
                args=(x[chunk],y[chunk],self._extent[0],self._extent[2],self.dx,self.dy,),
            )
        for proc in procs:
            indices_x, indices_y = proc.get()
            data[indices_y,indices_x] = True

        pool.close()
    
def calculate_indices_cpu(x,y,xmin,ymin,dx,dy):
    return ((x-xmin)/dx-0.5).astype(int,copy=False), ((y-ymin)/dy-0.5).astype(int,copy=False)

