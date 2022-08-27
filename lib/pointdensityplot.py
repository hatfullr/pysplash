import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from lib.scatterplot import ScatterPlot
import numpy as np

import globals

try:
    from numba import cuda
    has_jit = True
except ImportError:
    has_jit = False

class PointDensityPlot(ScatterPlot, object):
    def __init__(self, ax, x, y, s=1, **kwargs):
        # We should only need to check the y-axis for non-finite values,
        # because time should always be finite!
        valid = np.isfinite(y)
        x = x[valid]
        y = y[valid]

        self.unique_x = np.unique(x)
        self.xbins = None
        self.ybins = None
        
        super(PointDensityPlot,self).__init__(ax,x,y,s=s,**kwargs)

    def calculate_xypixels(self,*args,**kwargs):
        if globals.debug > 1: print("pointdensityplot.calculate_xypixels")
        super(PointDensityPlot,self).calculate_xypixels(*args,**kwargs)

        self.xbins = self.xpixels
        self.ybins = self.ypixels
        
        # Figure out the resolution that we should use on the x-axis
        if globals.time_mode:
            fig = self.ax.get_figure()
            pos = self.ax.get_position()
            figsize = fig.get_size_inches()
            self.xbins = int(fig.dpi * figsize[0] * pos.width)
            # If we will use more pixels than what is available from our data,
            # reduce the number of bins to instead fit the data
            if self.xbins > len(self.unique_x):
                dx = np.diff(self.unique_x)
                self.xbins = np.empty(len(self.unique_x)+1)
                self.xbins[0] = self.unique_x[0]
                self.xbins[-1] = self.unique_x[-1]
                self.xbins[1:-1] = self.unique_x[:-1] + 0.5*dx

    if has_jit:
        @staticmethod
        @cuda.jit('void(float32[:,:], float64[:], float64[:], float32, float32, float32, float32)')
        def calculate_gpu(data, y, x, ymin, xmin, invdy, invdx):
            i = cuda.grid(1)
            if i < y.shape[0]:
                cuda.atomic.add(
                    data,
                    (
                        int((y[i] - ymin)*invdy), # y index
                        int((x[i] - xmin)*invdx), # x index
                    ),
                    1 # Add 1
                )
        
        @profile
        def calculate_data_gpu(self,x,y,c):
            N = len(x)
            
            dx = (self._extent[1]-self._extent[0])/float(self.xbins)
            dy = (self._extent[3]-self._extent[2])/float(self.ybins)

            device_y = cuda.to_device(y)
            device_x = cuda.to_device(x)
            
            device_data = cuda.to_device(self._data.astype('float32'))
            
            blockspergrid = N // globals.threadsperblock + 1
            self.calculate_gpu[blockspergrid, globals.threadsperblock](
                device_data,
                device_y,
                device_x,
                self._extent[2]-0.5*dy,
                self._extent[0]-0.5*dx,
                1./dy,
                1./dx,
            )
            cuda.synchronize()
            data = device_data.copy_to_host()
            data /= np.amax(data)
            data[data == 0] = np.nan
            self._data = data

    def calculate_data_cpu(self,x,y,c):
        if globals.debug > 1: print("pointdensityplot.calculate_data_cpu")
        pixels,yedges,xedges = np.histogram2d(
            y,x,
            bins=[self.ybins,self.xbins],
        )
        # This step ensures that the bins appear centered
        dx = xedges[1]-xedges[0]
        dy = yedges[1]-yedges[0]
        self._extent = [
            np.amin(xedges) - 0.5*dx, # xmin
            np.amax(xedges) - 0.5*dx, # xmax
            np.amin(yedges) - 0.5*dy, # ymin
            np.amax(yedges) - 0.5*dy, # ymax
        ]

        pixels /= np.amax(pixles)
        pixels[pixels == 0] = np.nan
        
        self._data = pixels

