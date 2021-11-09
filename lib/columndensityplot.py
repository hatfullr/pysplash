import sys
if sys.version_info.major < 3:
    from customaxesimage import CustomAxesImage
else:
    from lib.customaxesimage import CustomAxesImage

import numpy as np
import math
from kernel import setupkernel,setupintegratedkernel
from scipy.integrate import simps
from globals import debug
if debug > 0: from time import time

try:
    from numba import cuda,float64
    import math
    has_jit = True
except ImportError:
    has_jit = False


class ColumnDensityPlot(CustomAxesImage,object):
    # m is mass of particles
    # h is radii of kernels
    def __init__(self,ax,x,y,m,h,u,**kwargs):
        self.ax = ax
        
        self.x = np.ascontiguousarray(x,dtype=np.double)
        self.y = np.ascontiguousarray(y,dtype=np.double)
        self.m = np.ascontiguousarray(m,dtype=np.double)
        self.h = np.ascontiguousarray(h,dtype=np.double)
        self.h2 = self.h**2
        self.u = np.ascontiguousarray(u,dtype=np.double)
        
        self.wint, self.ctab = setupintegratedkernel()
        self.wint = np.ascontiguousarray(self.wint,dtype=np.double)
        
        self.ctabinvh2 = self.ctab/self.h2

        if 'physical_units' in kwargs.keys() and 'display_units' in kwargs.keys():
            if kwargs['physical_units'] is not None and kwargs['display_units'] is not None:
                self.wint *= kwargs['physical_units'][3]**3

        if has_jit:
            self.stream = cuda.stream()
            N = len(self.x)
            
            self.device_x = cuda.device_array(N,dtype=np.double)
            self.device_y = cuda.device_array(N,dtype=np.double)
            self.device_m = cuda.device_array(N,dtype=np.double)
            self.device_h = cuda.device_array(N,dtype=np.double)
            self.device_h2 = cuda.device_array(N,dtype=np.double)
            self.device_ctabinvh2 = cuda.device_array(N,dtype=np.double)
            self.device_wint = cuda.device_array(len(self.wint),dtype=np.double)

            cuda.to_device(self.x,to=self.device_x,stream=self.stream)
            cuda.to_device(self.y,to=self.device_y,stream=self.stream)
            cuda.to_device(self.m,to=self.device_m,stream=self.stream)
            cuda.to_device(self.h,to=self.device_h,stream=self.stream)
            cuda.to_device(self.h2,to=self.device_h2,stream=self.stream)
            cuda.to_device(self.ctabinvh2,to=self.device_ctabinvh2,stream=self.stream)
            cuda.to_device(self.wint,to=self.device_wint,stream=self.stream)

            cuda.synchronize()

            #self.smallest_xpixels = None
            #self.smallest_ypixels = None
        #else:
            #self.smallest_xpixels = 10
            #self.smallest_ypixels = 10

        super(ColumnDensityPlot,self).__init__(
            self.ax,
            np.zeros((1,1),dtype=np.double),
            **kwargs
        )
        
        self.after_id = None
        
        self.first_draw = True


    #def set_data(self,*args,**kwargs):
    #    if has_jit:
    #        cuda.synchronize()
    #        super(ColumnDensityPlot,self).set_data(self._data.copy_to_host())
    #    else:
    #        super(ColumnDensityPlot,self).set_data(*args,**kwargs)

    """
    def refine(self,*args,**kwargs):
        #if self.after_id is not None:
        #    self.widget.after_cancel(self.after_id)
        #self.after_id = self.widget.after(10,self.refine)
        
        self.current_xpixels = min(2*self.current_xpixels,self.xpixels)
        self.current_ypixels = min(2*self.current_ypixels,self.ypixels)
        self.calculate()
    """

    # When calculate is called, we reset the refinement to the smallest pixel values,
    # calculate the data, update the plot, and then iteratively refine the image
    def calculate(self,*args,**kwargs):
        if debug > 0: start = time()
        # Reset the refinement
        #if self.smallest_xpixels is None: self.current_xpixels = self.xpixels
        #else: self.current_xpixels = self.smallest_xpixels
        #if self.smallest_ypixels is None: self.current_ypixels = self.ypixels
        #else: self.current_ypixels = self.smallest_ypixels

        # Calculate the data
        self.get_data()
        if debug > 0: print("columndensityplot: took %f seconds" % (time()-start))
    
    def get_data(self,*args,**kwargs):
        xmin,xmax = self.ax.get_xlim()
        ymin,ymax = self.ax.get_ylim()
        
        xpmin = self.x-self.h
        xpmax = self.x+self.h
        ypmin = self.y-self.h
        ypmax = self.y+self.h

        if self.physical_units is not None and self.display_units is not None:
            xpmin *= self.display_units[0]/self.physical_units[0]
            xpmax *= self.display_units[0]/self.physical_units[0]
            ypmin *= self.display_units[0]/self.physical_units[0]
            ypmax *= self.display_units[0]/self.physical_units[0]
        
        idx = np.logical_and(
            np.logical_and(
                np.logical_and(xpmax > xmin, xpmin < xmax),
                np.logical_and(ypmax > ymin, ypmin < ymax),
            ),
            self.u != 0,
        )
        
        if any(idx):
            self._extent = [xmin,xmax,ymin,ymax]
            self.dx = float(xmax-xmin)/float(self.xpixels)
            self.dy = float(ymax-ymin)/float(self.ypixels)
            self._data = np.zeros(np.shape(self._data),dtype=np.double)

            self.calculate_data(idx)
            
    #def after_calculate(self,*args,**kwargs):
        #vmin = np.nanmin(self._data[np.isfinite(self._data)])
        #vmax = np.nanmax(self._data[np.isfinite(self._data)])
        #self.set_clim(vmin,vmax)
        #print(self.colorbar)
        #self.colorbar.set_clim(vmin,vmax)
        
    if has_jit:
        @staticmethod
        @cuda.jit('void(double[:,:], int64[:], double[:], double[:], double[:], double[:], double[:], double, double, double, double, int64, int64, double[:], double[:])') # Decorator parameters improve performance
        def calculate_coldens_per_particle(data,idx,x,y,m,h,h2,dx,dy,xmin,ymin,xpixels,ypixels,ctabinvh2,wint):
            p = cuda.grid(1)
            if p < idx.size:
                i = idx[p]
                hi = h[i]
                h2i = h2[i]
                invh3i = 1./(hi*h2i)
                xi = x[i]
                yi = y[i]
                mi = m[i]
                ctabinvh2i = ctabinvh2[i]

                imin = max(int((xi-hi-xmin)/dx),0)
                imax = min(int((xi+hi-xmin)/dx)+1,xpixels)
                jmin = max(int((yi-hi-ymin)/dy),0)
                jmax = min(int((yi+hi-ymin)/dy)+1,ypixels)

                for ix in range(imin,imax):
                    xpos = xmin + (ix+0.5)*dx
                    dx2 = (xpos-xi)*(xpos-xi)
                    for jy in range(jmin,jmax):
                        ypos = ymin + (jy+0.5)*dy
                        dr2 = dx2 + (ypos-yi)*(ypos-yi)
                        if dr2 < h2i:
                            cuda.atomic.add(data, (jy,ix), mi*wint[int(dr2*ctabinvh2i)]*invh3i)

        
        def calculate_data(self,idx):
            # Do column density calculation on GPUs

            device_idx = cuda.to_device(np.where(idx)[0])
            device_data = cuda.to_device(np.zeros(np.shape(self._data)))

            xmin = self.ax.get_xlim()[0]
            ymin = self.ax.get_ylim()[0]
            dx = self.dx
            dy = self.dy
            if self.physical_units is not None and self.display_units is not None:
                xmin *= self.physical_units[0]/self.display_units[0]
                ymin *= self.physical_units[1]/self.display_units[1]
                dx *= self.physical_units[0]/self.display_units[0]
                dy *= self.physical_units[1]/self.display_units[1]
                
            threadsperblock = 512
            blockspergrid = len(idx) // threadsperblock + 1
            
            self.calculate_coldens_per_particle[blockspergrid,threadsperblock](
                device_data,
                device_idx,
                self.device_x,
                self.device_y,
                self.device_m,
                self.device_h,
                self.device_h2,
                dx,
                dy,
                xmin,
                ymin,
                self.xpixels,
                self.ypixels,
                self.device_ctabinvh2,
                self.device_wint,
            )
            cuda.synchronize()
            self._data = device_data.copy_to_host()
        
    else:
        def calculate_data(self,idx):
            # Calculate the column density for these LOSs (xpos,ypos).
            # Points along the LOS, zpos, are given and calculated outside this function
            # Returns an array of shape (len(xpos), len(ypos)). Each element of the
            # array is the column density at that (xpos, ypos).
            
            xmin,xmax = self.ax.get_xlim()
            ymin,ymax = self.ax.get_ylim()
            
            dx = self.dx
            dy = self.dy
            if self.physical_units is not None and self.display_units is not None:
                xmin *= self.physical_units[0]/self.display_units[0]
                xmax *= self.physical_units[0]/self.display_units[0]
                ymin *= self.physical_units[1]/self.display_units[1]
                ymax *= self.physical_units[1]/self.display_units[1]
                dx *= self.physical_units[0]/self.display_units[0]
                dy *= self.physical_units[1]/self.display_units[1]
            
            xpos = np.linspace(xmin,xmax,self.xpixels+1)[:-1] + 0.5*dx
            ypos = np.linspace(ymin,ymax,self.ypixels+1)[:-1] + 0.5*dy
            
            indexes = np.arange(len(self.x))[idx]
            x = self.x[idx]
            y = self.y[idx]
            h = self.h[idx]
            h2 = self.h2[idx]
            m = self.m[idx]
            ctabinvh2 = self.ctabinvh2[idx]
            invh3 = 1./(self.h*self.h2)
            
            dx = np.abs(xpos[:,None]-x)
            idx_xs = dx < h
            
            for i,(idx_x,dx_x) in enumerate(zip(idx_xs,dx)):
                if not any(idx_x): continue
                dx_x = dx_x[idx_x]
                
                dy = np.abs(ypos[:,None]-y[idx_x])
                idx_ys = dy < h[idx_x]
                for j,(idx_y,dy_y) in enumerate(zip(idx_ys,dy)):
                    if not any(idx_y): continue
                    dr2 = dx_x[idx_y]**2 + dy_y[idx_y]**2
                    
                    idx_r = dr2 < h2[idx_x][idx_y]
                    if not any(idx_r): continue
                    
                    indices = (dr2[idx_r]*ctabinvh2[idx_x][idx_y][idx_r]).astype(int,copy=False)
                    self._data[j,i] = sum(m[idx_x][idx_y][idx_r]*self.wint[indices]*invh3[idx_x][idx_y][idx_r])
                    

    def set_scale(self,*args,**kwargs):
        super(ColumnDensityPlot,self).set_scale(*args,**kwargs)
        self.after_calculate()
