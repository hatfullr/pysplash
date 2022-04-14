# The following function must take 1 input (float): u=r/h
# and returns the value of the kernel function, times h^3.

# Wendland C4 kernel
def kernel_function(u):
    # Expecting u = r/h as input, so scale it to our compact support
    q = u #u/compact_support
    return 495./(256.*np.pi)*(1.-q)**6*(35./3.*q**2.+6.*q+1.)


# ----------------------------------------------------------
# Don't change anything below here, except for "maxcoltable"
# and "nstp" if you really want to.
# ----------------------------------------------------------
maxcoltable = 1000 # Array size; SPLASH uses 1000
nstp = 100 # Integration steps; SPLASH uses 100

import numpy as np

# Set up the normal 3D kernel function (times h^3)
def setupkernel():
    u = np.linspace(0,1,maxcoltable,dtype=np.double)
    ctab = float(maxcoltable-1.)#/compact_support
    kernel = np.empty(maxcoltable)
    for i in range(maxcoltable):
        kernel[i] = kernel_function(u[i])
    return kernel,ctab

# Set up a 2D kernel function that is a "flattened" form
# of the 3D kernel function. The indices of the resulting
# array correspond to the 2D distance away from the center
# of the kernel. The value of each element is the integral
# through the entire 3D kernel at the given distance.
# The returned value is int_0^1 W(u')*h^3 du'
# We reduce the problem to two dimensions by setting
# y = 0 everywhere.
# u' = x/(kernel radius)
def setupintegratedkernel():
    integratedkernel = np.zeros(maxcoltable,dtype=np.double)
    kernel,ctab = setupkernel()
    
    # Now calculate the integral for all uprime values
    uprime = np.linspace(0,1,maxcoltable,dtype=np.double)
    for i in range(maxcoltable):
        # Integrate from a=0 to b, in steps of h
        b = np.sqrt(1**2.-uprime[i]**2.)
        h = b/float(nstp)

        # Obtain the integrand
        x = np.linspace(0,b,nstp)
        u = np.sqrt(x**2. + uprime[i]**2.)

        f = kernel[(ctab*u).astype(int,copy=False)]
        
        # Use trapezoidal rule
        integratedkernel[i] = 0.5*(f[0]+f[-1])*h
        integratedkernel[i] += np.sum(f[1:-1])*h
    integratedkernel *= 2 # Integrate through the entire kernel
    return integratedkernel,ctab


# For testing

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.style.use('supermongo')

    w,ctab = setupkernel()
    u = np.linspace(0,1,maxcoltable,dtype=np.double)
    itab = (ctab * u).astype(int,copy=False)
    #plt.plot(u,w[itab])
    #plt.show()
    
    intw,ctab = setupintegratedkernel()

    uprime = np.linspace(0,1,len(intw),dtype=np.double)
    itab = (ctab * uprime).astype(int,copy=False)
    y = intw[itab]
    
    plt.plot(uprime,y)
    plt.show()

