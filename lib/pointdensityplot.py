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
    import math
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

        self.ybins = np.linspace(self._extent[2],self._extent[3],self.ypixels+1)
        self.xbins = np.linspace(self._extent[0],self._extent[1],self.xpixels+1)

        #self.xpixels_to_xbin_end = np.ones(self.xpixels)
        #self.ypixels_to_ybin_end = np.ones(self.ypixels)
        
        # Figure out the resolution that we should use on the x-axis
        if globals.time_mode:
            # If we will use more pixels than what is available from our data,
            # reduce the number of bins to instead fit the data
            dx = np.diff(self.unique_x)
            self.xbins = np.empty(len(self.unique_x)+1)
            self.xbins[0] = self.unique_x[0] - 0.5*dx[0]
            self.xbins[-1] = self.unique_x[-1] + 0.5*dx[-1]
            self.xbins[1:-1] = self.unique_x[:-1] + 0.5*dx
            #dxpixels = (self._extent[1]-self._extent[0])/float(self.xpixels)
            #
            #for i in range(self.xpixels):
            #    xpos = self._extent[0] + dxpixels*i
            #    for xleft, xright in zip(self.xbins[:-1],self.xbins[1:]):
            #        if xleft <= xpos and xpos < xright:
            #            self.xpixels_to_xbin_end[i] = int(round((xright-xleft)/dxpixels))
            #            break

    if has_jit:
        def calculate_data_gpu(self,x,y,c):
            return self.calculate_data_cpu(x,y,c)
        """
        @staticmethod
        @cuda.jit#('void(float64[:,:], float64[:], float64[:], float64, float64, float64, float64)')
        def calculate_gpu(pixels, y, x, ymin, xmin, dypixel, dxpixel, ypixels_to_ybin_end, xpixels_to_xbin_end, N):
            i = cuda.grid(1)
            if i < N:
                # Find the bin which this particle belongs to
                #x[i] - min(xbins)

                # First find where the particle belongs in the pixels
                ix = int((x[i]-xmin)/dxpixel)
                jy = int((y[i]-ymin)/dypixel)

                # Now fill in the pixels that correspond to the bins
                for xpixel in range(ix, ix+xpixels_to_xbin_end[ix]):
                    cuda.atomic.add(pixels, (jy, xpixel), 1)
                
                #for ix,(xleft,xright) in enumerate(zip(xbins[:-1], xbins[1:])):
                #    if xleft <= x[i] and x[i] < xright:
                #        #print(xleft, x[i], xright)
                #        break
                #else: return
                #
                #for jy,(ybottom, ytop) in enumerate(zip(ybins[:-1], ybins[1:])):
                #    if ybottom <= y[i] and y[i] < ytop:
                #        break
                #else: return
                #print(jy,ix)
                #cuda.atomic.add(pixels, (jy,ix), 1)
                    
        
        def calculate_data_gpu(self,x,y,c):
            pixels = self._data.astype('float64')
            device_pixels = cuda.to_device(pixels)
            device_xpixels_to_xbin_end = cuda.to_device(self.xpixels_to_xbin_end)
            device_ypixels_to_ybin_end = cuda.to_device(self.ypixels_to_ybin_end)
            device_y = cuda.to_device(y)
            device_x = cuda.to_device(x)

            N = len(x)
            blockspergrid = N // globals.threadsperblock + 1
            self.calculate_gpu[blockspergrid, globals.threadsperblock](
                device_pixels,
                device_y,
                device_x,
                self._extent[2],
                self._extent[0],
                (self._extent[3]-self._extent[2])/float(pixels.shape[0]),
                (self._extent[1]-self._extent[0])/float(pixels.shape[1]),
                device_ypixels_to_ybin_end,
                device_xpixels_to_xbin_end,
                N,
            )
            cuda.synchronize()
            pixels = device_pixels.copy_to_host()#.reshape(self.ypixels,self.xpixels)
            pixels /= np.amax(pixels)
            pixels[pixels == 0] = np.nan
            self._data = pixels

            #print(self._extent)
        """
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

        pixels /= np.amax(pixels)
        pixels[pixels == 0] = np.nan
        
        self._data = pixels

