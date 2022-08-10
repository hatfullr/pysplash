import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from lib.scatterplot import ScatterPlot
import numpy as np

try:
    from numba import cuda
    has_jit = True
except ImportError:
    has_jit = False

class PointDensityPlot(ScatterPlot, object):
    def __init__(self, ax, x, y, s=1, **kwargs):
        super(PointDensityPlot,self).__init__(ax,x,y,s=s,**kwargs)
        
    if has_jit:
        def calculate_data_gpu(self,x,y,c):
            self.calculate_data_cpu(x,y,c)


    def calculate_data_cpu(self,x,y,c):
        x = np.array(x)
        y = np.array(y)
        if not np.array_equal(x.shape,y.shape):
            raise ValueError("x and y must have the same shape")

        # Set all non-finite numbers to NaN
        x[~np.isfinite(x)] = np.nan
        y[~np.isfinite(y)] = np.nan

        xmin, xmax = self._extent[0], self._extent[1]
        ymin, ymax = self._extent[2], self._extent[3]

        resolution = [self.xpixels,self.ypixels]

        dx = (xmax - xmin) / (resolution[0]-1)
        dy = (ymax - ymin) / (resolution[1]-1)
        dxy = np.array([dx,dy])

        xbins = np.linspace(xmin,xmax+dx,resolution[0])-0.5*dx
        ybins = np.linspace(ymin,ymax+dy,resolution[1])-0.5*dy

        valid = np.isfinite(y)
        pixels = np.histogram2d(
            y[valid],x[valid],
            bins=(ybins,xbins),
            density=False,
        )[0]

        #print(np.sum(pixels != 0))

        """
        if interpolate_empty:
            # If x is irregularly spaced, then there will be gaps in the
            # pixels on the x-axis. When this happens, we should fill in the
            # gaps using bilinear interpolation
            pixels2 = np.empty(pixels.shape)
            cols = []
            ndeleted = 0
            for col in range(pixels.shape[1]):
                if np.all(pixels[:,col] == 0):
                    cols.append(col)
                    pixels2 = np.delete(pixels2, col, axis=1)
                    ndeleted += 1
                else:
                    pixels2[:,col-ndeleted] = pixels[:,col]

            if pixels2.shape != pixels.shape:
                out = np.empty(pixels2.shape+tuple([2]),dtype=int)
                for j in range(out.shape[0]):
                    for i in range(out.shape[1]):
                        out[j][i] = (j,i)
                out = out.reshape((np.prod(pixels2.shape),2))
                pixels2 = pixels2.reshape(np.prod(pixels2.shape))
                interp = LinearNDInterpolator(out, pixels2, fill_value=0)

                yidxs = np.arange(pixels.shape[0])
                xidxs = np.empty(yidxs.shape)
                for col in cols:
                    xidxs[:] = col
                    pixels[:,col] = interp(yidxs, xidxs)
        """

        pixels /= np.nanmax(pixels)

        #if extent is None: extent = np.array([xmin,xmax,ymin,ymax])
        #if log: pixels = np.log10(pixels)
        pixels[pixels == 0] = np.nan
        
        self._data = pixels

        #return ax.imshow(pixels,origin=origin,extent=extent, **kwargs)
