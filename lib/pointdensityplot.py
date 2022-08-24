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
        valid = np.logical_and(np.isfinite(x),np.isfinite(y))
        x = x[valid]
        y = y[valid]

        self.unique_x = np.unique(x)
        self.calculated = False
        
        super(PointDensityPlot,self).__init__(ax,x,y,s=s,**kwargs)
        
    if has_jit:
        def calculate_data_gpu(self,x,y,c):
            self.calculate_data_cpu(x,y,c)

    def calculate_xypixels(self,*args,**kwargs):
        if globals.debug > 1: print("pointdensityplot.calculate_xypixels")
        super(PointDensityPlot,self).calculate_xypixels(*args,**kwargs)

        # Figure out the resolution that we should use on the x-axis
        if globals.time_mode:
            fig = self.ax.get_figure()
            pos = self.ax.get_position()
            figsize = fig.get_size_inches()
            rx = int(fig.dpi * figsize[0] * pos.width)
            self.xpixels = min(len(self.unique_x),rx)

    def calculate(self,*args,**kwargs):
        if globals.debug > 1: print("pointdensityplot.calculate")
        if not self.calculated:
            super(PointDensityPlot,self).calculate(*args,**kwargs)
        self.calculated = True

    def calculate_data_cpu(self,x,y,c):
        if globals.debug > 1: print("pointdensityplot.calculate_data_cpu")
        pixels,xedges,yedges = np.histogram2d(
            self.y,self.x,
            bins=[self.ypixels,self.xpixels],
            normed=True,
        )
        
        self._extent = [np.nanmin(yedges),np.nanmax(yedges),np.nanmin(xedges),np.nanmax(xedges)]

        pixels[pixels == 0] = np.nan
        
        self._data = pixels

