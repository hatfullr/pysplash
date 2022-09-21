import numpy as np

# This value gets set by the Data class on initialization,
# which happens whenever we read a data file. If the
# 'compact_support' keyword is not supplied by the function
# in read_file, then this value takes over as the default.
compact_support = 2

# The following function must take 1 input (float): u=r/h
# and returns the value of the kernel function, times h^3.

#"""
# Wendland C4 kernel
def kernel_function(u):
    # Expecting u = r/h with compact support 2h. Returns W * h^3
    q = 0.5*u
    return 495/(256*np.pi)*(1-q)**6*(35./3.*q**2+6*q+1)
#"""

"""
# Cubic spline kernel
def kernel_function(u):
    # Expecting u=r/h with compact support 2h. Returns W * h^3
    
    result = np.zeros(u.shape)
    idx0 = np.logical_and(0 <= u, u < 1)
    idx1 = np.logical_and(~idx0, u < 2)

    result[idx0] = 1+u**2*(0.75*u-1.5)
    result[idx1] = 0.25*(2-u)**3

    return result/np.pi
"""

# ----------------------------------------------------------
# Don't change anything below here, except for "maxcoltable"
# and "nstp" if you really want to.
# ----------------------------------------------------------
maxcoltable = 1000 # Array size; SPLASH uses 1000
nstp = 100 # Integration steps; SPLASH uses 100

# Set up the normal 3D kernel function (times h^3)
def setupkernel():
    # Our kernel functions expect compact support of 2h
    u = np.linspace(0,2,maxcoltable,dtype=np.double)
    # Note here than in order to get itab, you must do
    # int(ctab * (r/h)^2)
    ctab = float(maxcoltable-1)/compact_support**2
    kernel = np.empty(maxcoltable)
    for i in range(maxcoltable):
        kernel[i] = kernel_function(u[i])
    return kernel,ctab

# Set up a 2D kernel function that is a "flattened" form
# of the 3D kernel function. The indices of the resulting
# array correspond to the 2D distance away from the center
# of the kernel. The value of each element is the integral
# through the entire 3D kernel at the given distance.
# The returned value is int_0^(compact_support) W(u')*h^3 du'
# We reduce the problem to two dimensions by setting
# y = 0 everywhere.
# u' = x/h

"""
Imagine you are looking at a particle's kernel. Trace a
path through the kernel perpendicular to your line of
sight, like so:

                   x/h (integration path)
                   ^
             _____ |b
          .#`     `o.
        .`        /| `.
       /     r/h / |   \
      |         /  |a   |
      |        o---o----|-> q/h
      |                 |
       \               /
        .,           ,.
          `#._____.#`

We integrate the dimensionless quantity W*h^3 with respect
to x/h from a/h=0 to b/h = sqrt((r/h)^2 - (q/h)^2). Then we
multiply the result by 2 to integrate through the entire
kernel. Note that the result is a dimensionless quantity.
To use the result in calculations, you need to divide it
by h^2, because int W*h^3 d(x/h) = h^2 int W dx.
"""


def setupintegratedkernel():
    integratedkernel = np.zeros(maxcoltable,dtype=np.double)
    kernel,ctab = setupkernel()

    qoverh = np.linspace(0, compact_support, maxcoltable, dtype=np.double)
    for i, qoverhi in enumerate(qoverh):
        # Get the step sizes first
        boverh = np.sqrt(compact_support**2 - qoverhi**2)
        xoverh = np.linspace(0, boverh, nstp)

        # Now obtain the (squared) distances from the center of the kernel
        u2 = qoverhi**2 + xoverh**2

        # Get the corresponding kernel function values
        f = kernel[(ctab*u2).astype(int,copy=False)]

        # Get the step sizes
        stepsize = boverh/float(len(xoverh))
        
        # Use trapezoidal rule
        integratedkernel[i] = 0.5*(f[0]+f[-1])*stepsize
        integratedkernel[i] += np.sum(f[1:-1])*stepsize

    integratedkernel *= 2
    
    return integratedkernel,ctab


# For testing
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    h = 1

    w,ctab = setupkernel()
    r = np.linspace(0,compact_support*h,maxcoltable,dtype=np.double)
    u = r/h
    itab = (ctab * u**2).astype(int,copy=False)
    y = w[itab]/h**3
    plt.plot(u,y,label="$W$")
    
    intw,ctab = setupintegratedkernel()

    r = np.linspace(0,compact_support*h,len(intw),dtype=np.double)
    u = r/h
    itab = (ctab * u**2).astype(int,copy=False)
    y = intw[itab]/h**2
    
    plt.plot(u,y,label="$\\int W$")
    plt.legend()
    plt.show()

