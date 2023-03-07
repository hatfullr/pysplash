import sys
if sys.version_info.major < 3:
    from customaxesimage import CustomAxesImage
else:
    from lib.customaxesimage import CustomAxesImage

import numpy as np
import math
import kernel
import globals
from time import time
from collections import Counter
if globals.debug > 0: import time

try:
    from numba import cuda, types
    has_jit = True
except ImportError:
    has_jit = False

class SurfaceValuePlot(CustomAxesImage,object):
    def __init__(self,ax,A,x,y,z,h,physical_units,display_units,**kwargs):
        if globals.debug > 1: print("surfacevalueplot.__init__")
        self.ax = ax

        # We are calculating integral sum(m * A / rho * W) dz where
        # m is mass, A is a given quantity, rho is density, and W is
        # the kernel function. We must have the same units on the
        # x and y axes or else this calculation makes no sense.
        #print(physical_units)
        if physical_units[1] != physical_units[2]:
            raise ValueError("Cannot calculate a surface value plot that has different units on the x and y axes")

        self.A = np.ascontiguousarray(A,dtype=np.double)
        self.x = np.ascontiguousarray(x,dtype=np.double)
        self.y = np.ascontiguousarray(y,dtype=np.double)
        self.z = np.ascontiguousarray(z,dtype=np.double)
        self.size = np.ascontiguousarray(kernel.compact_support*h,dtype=np.double)
        self.size2 = self.size**2

        physical_quantity_unit = physical_units[0]
        display_quantity_unit = display_units[0]

        physical_unit = physical_quantity_unit
        display_unit = display_quantity_unit
        
        self.units = physical_unit / display_unit

        super(SurfaceValuePlot,self).__init__(
            self.ax,
            np.full((1,1),np.nan,dtype=np.double),
            **kwargs
        )


    def calculate(self,*args,**kwargs):
        if globals.debug > 1: print("surfacevalueplot.calculate")
        if globals.debug > 0: start = time.time()

        xmin,xmax = self.ax.get_xlim()
        ymin,ymax = self.ax.get_ylim()
        
        xpmin = self.x-self.size
        xpmax = self.x+self.size
        ypmin = self.y-self.size
        ypmax = self.y+self.size
        
        idx = np.logical_and(
            np.logical_and(xpmax > xmin, xpmin < xmax),
            np.logical_and(ypmax > ymin, ypmin < ymax),
        )
        if any(idx):
            self._extent = [xmin,xmax,ymin,ymax]
            self.dx = float(xmax-xmin)/float(self.xpixels) #* display_to_physical[1]
            self.dy = float(ymax-ymin)/float(self.ypixels) #* display_to_physical[2]
            
            self._data = np.full(np.shape(self._data),np.nan,dtype=np.double)
            self.calculate_data(idx)
            #self._data *= self.units / self.cunits
        if globals.debug > 0: print("surfacevalueplot.calculate took %f seconds" % (time.time()-start))

    
    if has_jit:
        @staticmethod
        @cuda.jit('void(double[:,:], double[:], double[:], double[:], double[:], double[:], double, double, double, double, int64, int64)') # Decorator parameters improve performance
        def calculate_gpu(data,A,x,y,z,size2,xmin,ymin,dx,dy,xpixels,ypixels):
            j,i = cuda.grid(2)
            if i < xpixels and j < ypixels:
                xpos = xmin + (i+0.5) * dx
                ypos = ymin + (j+0.5) * dy
                
                zmin = math.inf
                for p in range(len(x)):
                    dxpos = x[p]-xpos
                    dypos = y[p]-ypos
                    dz2 = size2[p] - dxpos*dxpos - dypos*dypos
                    if dz2 > 0:
                        zminp = z[p] - math.sqrt(dz2)
                        if zminp < zmin:
                            data[j,i] = A[p]
                            zmin = zminp

    def calculate_data_gpu(self,idx): # On GPU
        if globals.debug > 1: print("surfacevalueplot.calculate_data_gpu")

        device_idx = cuda.to_device(np.where(idx)[0])
        device_data = cuda.to_device(np.ascontiguousarray(self._data))

        xmin = self.ax.get_xlim()[0]
        ymin = self.ax.get_ylim()[0]

        device_A = cuda.to_device(np.ascontiguousarray(self.A[idx],dtype=np.double))
        device_x = cuda.to_device(np.ascontiguousarray(self.x[idx],dtype=np.double))
        device_y = cuda.to_device(np.ascontiguousarray(self.y[idx],dtype=np.double))
        device_z = cuda.to_device(np.ascontiguousarray(self.z[idx],dtype=np.double))
        device_size2 = cuda.to_device(np.ascontiguousarray(self.size2[idx],dtype=np.double))

        # For the slower method that does work
        ndims = len(self._data.shape)
        threadsperblock = np.full(ndims, int(globals.threadsperblock**(1./ndims)), dtype=int)
        blockspergrid = np.array(self._data.shape,dtype=int) // threadsperblock + 1
        
        self.calculate_gpu[tuple(blockspergrid),tuple(threadsperblock)](
            device_data,
            device_A,
            device_x,
            device_y,
            device_z,
            device_size2,
            xmin,
            ymin,
            self.dx,
            self.dy,
            self.xpixels,
            self.ypixels,
        )
        globals.gpu_busy = True
        cuda.synchronize()
        globals.gpu_busy = False
        self._data = device_data.copy_to_host()

    def calculate_data_cpu(self,idx): # On CPU
        if globals.debug > 1: print("surfacevalueplot.calculate_data_cpu")

        xmin,xmax = self.ax.get_xlim()
        ymin,ymax = self.ax.get_ylim()

        xpos = np.linspace(xmin,xmax,self.xpixels+1)[:-1] + 0.5*self.dx
        ypos = np.linspace(ymin,ymax,self.ypixels+1)[:-1] + 0.5*self.dy

        A = self.A[idx]
        x = self.x[idx]
        y = self.y[idx]
        z = self.z[idx]
        size2 = self.size2[idx]

        # This is the fastest I could get the routine to run. It's not readable.
        # Sorry about that. I sold my soul to the devil for optimizations...

        try:
            dx2s = (x - xpos[:,None])**2
            dy2s = (y - ypos[:,None])**2

            drprime2s = dx2s[:,None] + dy2s
            dzs = np.sqrt(size2 - drprime2s)
            zmins = z - dzs

            idx_xys = drprime2s < size2
            valids = np.any(idx_xys,axis=2)

            js = np.array([np.arange(self.ypixels,dtype=int)] * self.xpixels)
            zmins[np.isnan(zmins)] = np.inf
            idx_mins = np.argmin(zmins,axis=2)

            for i in range(self.xpixels):
                for j in js[i][valids[i]]:
                    self._data[j,i] = A[idx_mins[i,j]]
        except np.core._exceptions._ArrayMemoryError:
            print("This could take a while...")
            if sys.version_info.major < 3:
                print("You are using Python 2. Use Python 3 if you have a GPU on this machine.")
            for i in range(self.xpixels):
                print("Progress = %3.2f%%" % (float(i)/self.xpixels * 100))
                dx2s = (x - xpos[i])**2
                for j in range(self.ypixels):
                    drprime2s = dx2s + (y-ypos[j])**2
                    idx_xy = drprime2s < size2
                    if not np.any(idx_xy): continue

                    dz2 = size2 - drprime2s
                    idx = dz2 > 0
                    zmin = z[idx] - np.sqrt(dz2[idx])
                    self._data[j,i] = A[np.argmin(zmin)]

    def calculate_data(self,*args,**kwargs):
        if not has_jit or globals.gpu_busy: return self.calculate_data_cpu(*args,**kwargs)
        else: return self.calculate_data_gpu(*args,**kwargs)
