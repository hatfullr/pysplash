import globals
import numpy as np

def rotate(x,y,z,anglexdeg,angleydeg,anglezdeg):
    if globals.debug > 1: print("rotate.rotate")
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
