import sys
if sys.version_info.major < 3:
    from customaxesimage import CustomAxesImage
else:
    from lib.customaxesimage import CustomAxesImage

import numpy as np
import math
import kernel
import globals
if globals.debug > 0: from time import time

try:
    from numba import cuda
    has_jit = True
except ImportError:
    has_jit = False

class IntegratedValuePlot(CustomAxesImage,object):
    def __init__(self,ax,A,x,y,m,h,rho,physical_units,display_units,**kwargs):
        if globals.debug > 1: print("integratedvalueplot.__init__")
        self.ax = ax

        # We are calculating integral sum(m * A / rho * W) dz where
        # m is mass, A is a given quantity, rho is density, and W is
        # the kernel function. We must have the same units on the
        # x and y axes or else this calculation makes no sense.
        #print(physical_units)
        if physical_units[1] != physical_units[2]:
            raise ValueError("Cannot calculate an integrated value plot that has different units on the x and y axes")

        self.A = np.ascontiguousarray(A,dtype=np.double)
        self.x = np.ascontiguousarray(x,dtype=np.double)
        self.y = np.ascontiguousarray(y,dtype=np.double)
        self.m = np.ascontiguousarray(m,dtype=np.double)
        self.h = np.ascontiguousarray(h,dtype=np.double)
        self.rho = np.ascontiguousarray(rho,dtype=np.double)

        # We are given all the quantities in display units. For now,
        # we want to show integrated value plots only in physical units.
        
        physical_quantity_unit = physical_units[0]
        physical_length_unit = physical_units[1]
        physical_mass_unit = physical_units[3]
        physical_density_unit = physical_units[5]
        display_quantity_unit = display_units[0]
        display_length_unit = display_units[1]
        display_mass_unit = display_units[3]
        display_density_unit = display_units[5]

        physical_unit = physical_mass_unit * physical_quantity_unit / physical_density_unit * physical_length_unit / physical_length_unit**2
        display_unit = display_mass_unit * display_quantity_unit / display_density_unit * display_length_unit / display_length_unit**2
        
        self.units = physical_unit / display_unit

        self.wint, self.ctab = kernel.setupintegratedkernel()
        self.wint = np.ascontiguousarray(self.wint,dtype=np.double)

        self.h2 = self.h**2
        self.ctabinvh2 = self.ctab/self.h2
        self.quantity = np.ascontiguousarray(
            self.m*self.A/self.rho,
            dtype=np.double,
        )

        if has_jit:
            self.stream = cuda.stream()
            N = len(self.x)
            self.device_x = cuda.device_array(N,dtype=np.double)
            self.device_y = cuda.device_array(N,dtype=np.double)
            self.device_quantity = cuda.device_array(N,dtype=np.double)
            self.device_h = cuda.device_array(N,dtype=np.double)
            self.device_h2 = cuda.device_array(N,dtype=np.double)
            self.device_ctabinvh2 = cuda.device_array(N,dtype=np.double)
            self.device_wint = cuda.device_array(len(self.wint),dtype=np.double)

            cuda.to_device(self.x,to=self.device_x,stream=self.stream)
            cuda.to_device(self.y,to=self.device_y,stream=self.stream)
            cuda.to_device(self.quantity,to=self.device_quantity,stream=self.stream)
            cuda.to_device(self.h,to=self.device_h,stream=self.stream)
            cuda.to_device(self.h2,to=self.device_h2,stream=self.stream)
            cuda.to_device(self.ctabinvh2,to=self.device_ctabinvh2,stream=self.stream)
            cuda.to_device(self.wint,to=self.device_wint,stream=self.stream)

            globals.gpu_busy = True
            cuda.synchronize()
            globals.gpu_busy = False

        super(IntegratedValuePlot,self).__init__(
            self.ax,
            np.zeros((1,1),dtype=np.double),
            **kwargs
        )


    def calculate(self,*args,**kwargs):
        if globals.debug > 1: print("integratedvalueplot.calculate")
        if globals.debug > 0: start = time()

        xmin,xmax = self.ax.get_xlim()
        ymin,ymax = self.ax.get_ylim()
        
        xpmin = self.x-kernel.compact_support*self.h
        xpmax = self.x+kernel.compact_support*self.h
        ypmin = self.y-kernel.compact_support*self.h
        ypmax = self.y+kernel.compact_support*self.h
        
        """
        display_to_physical = [pu/du for pu,du in zip(self.physical_units,self.display_units)]
        
        idx = np.logical_and(
                np.logical_and(xpmax > xmin*display_to_physical[1], xpmin < xmax*display_to_physical[1]),
                np.logical_and(ypmax > ymin*display_to_physical[2], ypmin < ymax*display_to_physical[2]),
        )
        """
        idx = np.logical_and(
            np.logical_and(xpmax > xmin, xpmin < xmax),
            np.logical_and(ypmax > ymin, ypmin < ymax),
        )
        if any(idx):
            self._extent = [xmin,xmax,ymin,ymax]
            self.dx = float(xmax-xmin)/float(self.xpixels) #* display_to_physical[1]
            self.dy = float(ymax-ymin)/float(self.ypixels) #* display_to_physical[2]
            
            self._data = np.zeros(np.shape(self._data),dtype=np.double)
            self.calculate_data(idx)
            #self._data *= self.units / self.cunits
        if globals.debug > 0: print("integratedvalueplot.calculate took %f seconds" % (time()-start))

    
    if has_jit:
        @staticmethod
        @cuda.jit('void(double[:,:], int64[:], double[:], double[:], double[:], double[:], double[:], double, double, double, double, int64, int64, double[:], double[:], double)') # Decorator parameters improve performance
        def calculate_gpu(data,idx,x,y,quantity,h,h2,dx,dy,xmin,ymin,xpixels,ypixels,ctabinvh2,wint,compact_support):
            p = cuda.grid(1)
            if p < idx.size:
                i = idx[p]
                hi = h[i]
                h2i = h2[i]
                invh2i = 1. / h2i
                xi = x[i]
                yi = y[i]
                quantityi = quantity[i]
                ctabinvh2i = ctabinvh2[i]

                imin = max(int((xi-compact_support*hi-xmin)/dx),0)
                imax = min(int((xi+compact_support*hi-xmin)/dx)+1,xpixels)
                jmin = max(int((yi-compact_support*hi-ymin)/dy),0)
                jmax = min(int((yi+compact_support*hi-ymin)/dy)+1,ypixels)
                
                for ix in range(imin,imax):
                    xpos = xmin + (ix+0.5)*dx
                    dx2 = (xpos-xi)*(xpos-xi)
                    for jy in range(jmin,jmax):
                        ypos = ymin + (jy+0.5)*dy
                        dr2 = dx2 + (ypos-yi)*(ypos-yi)
                        if dr2 < compact_support*compact_support*h2i:
                            cuda.atomic.add(data, (jy,ix), quantityi*wint[int(dr2*ctabinvh2i)]*invh2i)
        
    def calculate_data_gpu(self,idx): # On GPU
        if globals.debug > 1: print("integratedvalueplot.calculate_data")

        device_idx = cuda.to_device(np.where(idx)[0])
        device_data = cuda.to_device(self._data)

        #display_to_physical = [pu/du for pu,du in zip(self.physical_units,self.display_units)]

        xmin = self.ax.get_xlim()[0]#*display_to_physical[1]
        ymin = self.ax.get_ylim()[0]#*display_to_physical[2]

        blockspergrid = len(idx) // globals.threadsperblock + 1

        self.calculate_gpu[blockspergrid,globals.threadsperblock](
            device_data,
            device_idx,
            self.device_x,
            self.device_y,
            self.device_quantity,
            self.device_h,
            self.device_h2,
            self.dx,
            self.dy,
            xmin,
            ymin,
            self.xpixels,
            self.ypixels,
            self.device_ctabinvh2,
            self.device_wint,
            kernel.compact_support,
        )
        globals.gpu_busy = True
        cuda.synchronize()
        globals.gpu_busy = False
        self._data = device_data.copy_to_host()

    def calculate_data_cpu(self,idx): # On CPU
        if globals.debug > 1: print("integratedvalueplot.calculate_data")

        xmin,xmax = self.ax.get_xlim()
        ymin,ymax = self.ax.get_ylim()

        xpos = np.linspace(xmin,xmax,self.xpixels+1)[:-1] + 0.5*self.dx
        ypos = np.linspace(ymin,ymax,self.ypixels+1)[:-1] + 0.5*self.dy

        x = self.x[idx]
        y = self.y[idx]
        h = self.h[idx]
        h2 = self.h2[idx]
        invh2 = 1./self.h2
        quantity = self.quantity[idx]
        ctabinvh2 = self.ctabinvh2[idx]
        size2 = (kernel.compact_support*h)**2

        dx2 = (xpos[:,None]-x)**2
        idx_xs = dx2 < size2

        for i,(idx_x,dx2_x) in enumerate(zip(idx_xs,dx2)):
            if not any(idx_x): continue
            dx2_x = dx2_x[idx_x]

            dy2 = (ypos[:,None]-y[idx_x])**2
            idx_ys = dy2 < size2[idx_x]
            for j,(idx_y,dy2_y) in enumerate(zip(idx_ys,dy2)):
                if not any(idx_y): continue
                dr2 = dx2_x[idx_y] + dy2_y[idx_y]

                idx_r = dr2 < size2[idx_x][idx_y]
                if not any(idx_r): continue

                indices = (ctabinvh2[idx_x][idx_y][idx_r] * dr2[idx_r]).astype(int,copy=False)
                self._data[j,i] = sum(quantity[idx_x][idx_y][idx_r]*self.wint[indices]*invh2[idx_x][idx_y][idx_r])

    def calculate_data(self,*args,**kwargs):
        if not has_jit or globals.gpu_busy: return self.calculate_data_cpu(*args,**kwargs)
        else: return self.calculate_data_gpu(*args,**kwargs)
