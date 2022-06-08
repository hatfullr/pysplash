"""
Modify the function below to read in your own data
files of any format. The function must take as input
only one file name and provide as output a
dictionary object. The dictionary object will have 3
keys: 'data', 'display_units', and 'physical_units'.
The values for each of the keys will be an
OrderedDict with the following keys:
    Required:
        'x':  array-like  x positions
        'y':  array-like  y positions
        'z':  array-like  z positions
        'm':  array-like  masses
        'h':  array-like  smoothing lengths
    Optional:
        'u':  array-like  internal energy
        't':  float,int   time
All particle arrays must have the same length. For
column density plots, 'u' is required. Any other keys
that you specify that contain array-like objects of
the same length as 'x' will be detected as a
plottable value.

If you include 't' as a key, the time associated with
each file will be shown on the plot.

It is assumed that particles with u=0 are special 
particles that will not contribute to the column 
density (StarSmasher default).

VISUALIZING PRE-COMPUTED IMAGE DATA:
If you just want to view data from an output file that
is already organized as an image (a 2D array of data),
simply have read_data return an OrderedDict with two
keys: 'image' and 'extent', where 'image' is the 2D
data and 'extent' is the bounding box of that data.
See the function "fluxcal_teff" below for an example.

The default file read protocol is set to read out*.sph
files from StarSmasher output.

For example, if my data file has only x and y data, in
units of solar radii, the returned object would look 
like this:

to_return = {
    'data': OrderedDict(
       'x': np.array([1.,2.,3.,4.]),
       'y': np.array([1.,2.,3.,4.]),
    ),
    'display_units': OrderedDict(
       'x': 1., # Display in units of solar radii
       'y': 1., # Display in units of solar radii
    ),
    'physical_units': OrderedDict(
        'x': 6.9599e10, # Solar radius in cm
        'y': 6.9599e10, # Solar radius in cm
    ),
}

If I had a data file with x and y data only, in units
of cm, and I wanted to display them in units of solar
radii, I would return this object:

to_return = {
    'data': OrderedDict(
       'x': [1.,2.,3.,4.],
       'y': [1.,2.,3.,4.],
    ),
    'display_units': OrderedDict(
       'x': 1./6.9599e10, # Display in units of solar radii
       'y': 1./6.9599e10, # Display in units of solar radii
    ),
    'physical_units': OrderedDict(
        'x': 1., # Already in cgs units
        'y': 1., # Already in cgs units
    ),
}

"""

from collections import OrderedDict

from lib.fastfileread import FastFileRead
from lib.fastfileread import read_starsmasher
import numpy as np
from globals import debug
import os.path
import fnmatch

def read_file(filename):
    # Supported pattern types are "*", "?", "[seq]", and "[!seq]"
    # see https://docs.python.org/3/library/fnmatch.html for details
    codes = {
        "starsmasher" : [
            ["out*.sph*",starsmasher],
            ["restartrad*.sph*",starsmasher],
        ],
        "fluxcal" : [
            ["fluxcal*.track*",fluxcal_track],
            ["teffs*.dat*",fluxcal_teff],
        ],
        "mesa" : [
            ["*.mesa*", mesa],
            ["*profile*.data*", mesa],
        ],
    }
    
    basename = os.path.basename(filename)
    for key, val in codes.items():
        for pattern,method in val:
            if fnmatch.fnmatch(basename,pattern):
                return method(filename)
                break
        else: continue # Only if the inner loop didn't break
        break # Only if the inner loop did break
    else: # Only if the inner loop didn't break
        raise ValueError("File name '"+basename+"' does not match any of the accepted patterns in read_file")



# For out*.sph files from StarSmasher
def starsmasher(filename):
    munit = 1.9891e33
    runit = 6.9599e10
    gravconst = 6.67390e-8
    tunit = np.sqrt(runit**3/(munit*gravconst))
    vunit = np.sqrt(gravconst*munit/runit)
    dvdtunit = gravconst * munit / runit**2.
    eunit = gravconst*munit/runit
    edotunit = np.sqrt(gravconst**3. * munit**5. / runit**7.)
    display_units = [
        1., # x
        1., # y
        1., # z
        1., # m
        1., # h
        1., # rho
        vunit, # vx
        vunit, # vy
        vunit, # vz
        dvdtunit, # vxdot
        dvdtunit, # vydot
        dvdtunit, # vzdot
        eunit, # u
        edotunit, # udot
        eunit, # grpot
        1., # meanmolecular
        1., # cc
        1., # divv
        eunit, # ueq
        1., # tthermal
        1., # opacity (already in cgs)
        1., # uraddot (already in cgs)
        1., # temperature
        1., # avgtau
    ]

    physical_units = [
        runit, # x
        runit, # y
        runit, # z
        munit, # m
        runit, # h
        munit/runit**3., # rho
        vunit, # vx
        vunit, # vy
        vunit, # vz
        dvdtunit, # vxdot
        dvdtunit, # vydot
        dvdtunit, # vzdot
        eunit, # u
        edotunit, # udot
        eunit, # grpot
        1., # meanmolecular
        1., # cc
        1., # divv
        eunit, # ueq
        1., # tthermal
        1., # opacity
        1., # uraddot
        1., # temperature
        1., # avgtau
    ]

    data, header = read_starsmasher(filename, return_headers=True)

    # Correct some common header names
    names = list(data._data.dtype.names)
    if "hp" in names:
        names[names.index("hp")] = "h"
    if "am" in names:
        names[names.index("am")] = "m"
    data._data.dtype.names = tuple(names)
    
    to_return = {
        'data'           : OrderedDict(),
        'display_units'  : OrderedDict(),
        'physical_units' : OrderedDict(),
    }
    
    for i,dname in enumerate(data._data.dtype.names):
        to_return['data'][dname] = data[dname]
        to_return['display_units'][dname] = display_units[i]
        to_return['physical_units'][dname] = physical_units[i]
    to_return['data']['t'] = header._data['t'][0]
    to_return['display_units']['t'] = tunit / 3600. / 24. # In days
    to_return['physical_units']['t'] = tunit
    
    return to_return





# For fluxcal*.track files from FluxCal
def fluxcal_track(filename):
    munit = 1.9891e33
    runit = 6.9599e10
    display_units = [
        1./runit, # x
        1./runit, # y
        1./runit, # z
        1., # m
        1., # h
        1., # rho
        1., # u
        1., # mu
        1., # g
        1., # T_SPH
        1., # Teff
        1., # P
        1., # P_env
        1., # P_surf
        1., # opacity
        1., # opacity_surf
        1., # rho_surf
        1., # tau
        1., # entropy
        1, # ID
    ]
    
    with open(filename) as f:
        header = f.readline().split()
    data = FastFileRead(
        filename,
        header=1,
        parallel=False,
        verbose=debug > 1,
    )

    # Correct some common header names
    names = list(data._data.dtype.names)
    if "hp" in names:
        names[names.index("hp")] = "h"
    if "am" in names:
        names[names.index("am")] = "m"
    data._data.dtype.names = tuple(names)
    
    to_return = {
        'data'           : OrderedDict(),
        'display_units'  : OrderedDict(),
        'physical_units' : OrderedDict(),
    }
    
    for i,key in enumerate(header):
        if key == 'T_SPH': key = 'temperature'
        to_return['data'][key] = data[:,i]
        to_return['display_units'][key] = display_units[i]
        to_return['physical_units'][key] = 1.
        
    return to_return

# teffs*.dat files from FluxCal
def fluxcal_teff(filename):
    data = OrderedDict()
    with open(filename,'r') as f:
        header = f.readline().split()
    xmin = string_to_float(header[0])
    dx = string_to_float(header[1])
    Nx = int(header[2])
    ymin = string_to_float(header[3])
    dy = string_to_float(header[4])
    Ny = int(header[5])

    data['image'] = np.loadtxt(filename,skiprows=1)
    data['extent'] = [xmin,xmin+dx*Nx,ymin,ymin+dy*Ny]

    return data

def mesa(filename):
    to_return = {
        'data'           : OrderedDict(),
        'display_units'  : OrderedDict(),
        'physical_units' : OrderedDict(),
    }

    with open(filename,'r') as f:
        f.readline()
        h = f.readline().split()
        line = f.readline().split()
        num_zones = int(line[h.index("num_zones")])

        f.readline()
        f.readline()

        header = f.readline().split()

        data = np.empty((num_zones,len(header)),dtype=float)
        for i,line in enumerate(f):
            data[i] = line.split()

    for i, key in enumerate(header):
        to_return['data'][key] = data[:,i]
        to_return['display_units'][key] = 1.
        to_return['physical_units'][key] = 1.

    return to_return
