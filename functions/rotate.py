import globals
import numpy as np

try:
    from numba import cuda
    import math
    has_jit = True
except ImportError:
    has_jit = False

if has_jit:
    @cuda.jit('void(float64[:], float64[:], float64[:], int32, float64, float64, float64)')
    def rotate_gpu_kernel(x,y,z,N,xangle,yangle,zangle):
        i = cuda.grid(1)
        if i < N:
            xi = x[i]
            yi = y[i]
            zi = z[i]
            
            if zangle != 0: # rotate about z
                rold = math.sqrt(xi*xi + yi*yi)
                phi = math.atan2(yi,xi)
                phi -= zangle
                xi = rold*math.cos(phi)
                yi = rold*math.sin(phi)
            if yangle != 0: # rotate about y
                rold = math.sqrt(zi*zi + xi*xi)
                phi = math.atan2(zi,xi)
                phi -= yangle
                zi = rold*math.sin(phi)
                xi = rold*math.cos(phi)
            if xangle != 0: # rotate about x
                rold = math.sqrt(yi*yi + zi*zi)
                phi = math.atan2(zi,yi)
                phi -= xangle
                yi = rold*math.cos(phi)
                zi = rold*math.sin(phi)

            x[i] = xi
            y[i] = yi
            z[i] = zi

def rotate_gpu(x,y,z,anglexdeg,angleydeg,anglezdeg):
    if globals.debug > 1: print("rotate.rotate")
    if isinstance(x, (float,int)): x = [x]
    if isinstance(y, (float,int)): y = [y]
    if isinstance(z, (float,int)): z = [z]
    
    if not isinstance(x,np.ndarray): x = np.array(x)
    if not isinstance(y,np.ndarray): y = np.array(y)
    if not isinstance(z,np.ndarray): z = np.array(z)

    xangle = float(anglexdeg)/180.*np.pi
    yangle = float(angleydeg)/180.*np.pi
    zangle = float(anglezdeg)/180.*np.pi

    N = len(x)
    if len(y) != N or len(z) != N:
        raise Exception("x, y, and z arrays must have the same size")

    device_x = cuda.to_device(np.ascontiguousarray(x,dtype='float64'))
    device_y = cuda.to_device(np.ascontiguousarray(y,dtype='float64'))
    device_z = cuda.to_device(np.ascontiguousarray(z,dtype='float64'))

    blockspergrid = N // globals.threadsperblock + 1
    rotate_gpu_kernel[blockspergrid,globals.threadsperblock](
        device_x,
        device_y,
        device_z,
        N,
        xangle,
        yangle,
        zangle,
    )
    globals.gpu_busy = True
    cuda.synchronize()
    globals.gpu_busy = False
    return device_x.copy_to_host(), device_y.copy_to_host(), device_z.copy_to_host()


def rotate_cpu(x,y,z,anglexdeg,angleydeg,anglezdeg):
    if globals.debug > 1: print("rotate.rotate")

    if isinstance(x, (float,int)): x = [x]
    if isinstance(y, (float,int)): y = [y]
    if isinstance(z, (float,int)): z = [z]

    if not isinstance(x,np.ndarray): x = np.array(x)
    if not isinstance(y,np.ndarray): y = np.array(y)
    if not isinstance(z,np.ndarray): z = np.array(z)
    
    xangle = float(anglexdeg)/180.*np.pi
    yangle = float(angleydeg)/180.*np.pi
    zangle = float(anglezdeg)/180.*np.pi

    if zangle != 0: # rotate about z
        rold = np.sqrt(x*x + y*y)
        phi = np.arctan2(y,x)
        phi -= zangle
        x = rold*np.cos(phi)
        y = rold*np.sin(phi)
    if yangle != 0: # rotate about y
        rold = np.sqrt(z*z + x*x)
        phi = np.arctan2(z,x)
        phi -= yangle
        z = rold*np.sin(phi)
        x = rold*np.cos(phi)
    if xangle != 0: # rotate about x
        rold = np.sqrt(y*y + z*z)
        phi = np.arctan2(z,y)
        phi -= xangle
        y = rold*np.cos(phi)
        z = rold*np.sin(phi)

    return x, y, z

def rotate(*args,**kwargs):
    if not has_jit or globals.gpu_busy: return rotate_cpu(*args,**kwargs)
    else: return rotate_gpu(*args,**kwargs)
