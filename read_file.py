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
    header_names = [
        'ntot',
        'nnopt',
        'hco',
        'hfloor',
        'sep0',
        'tf',
        'dtout',
        'nout',
        'nit',
        't',
        'nav',
        'alpha',
        'beta',
        'tjumpahead',
        'ngr',
        'nrelax',
        'trelax',
        'dt',
        'omega2',
        'ncooling',
        'erad',
        'ndisplace',
        'displacex',
        'displacey',
        'displacez',
    ]

    header_format = [
        'i4', # ntot
        'i4', # nnopt
        'f8', # hco
        'f8', # hfloor
        'f8', # sep0
        'f8', # tf
        'f8', # dtout
        'i4', # nout
        'i4', # nit
        'f8', # t
        'i4', # nav
        'f8', # alpha
        'f8', # beta
        'f8', # tjumpahead
        'i4', # ngr
        'i4', # nrelax
        'f8', # trelax
        'f8', # dt
        'f8', # omega2
        'i4', # ncooling
        'f8', # erad
        'i4', # ndisplace
        'f8', # displacex
        'f8', # displacey
        'f8', # displacez
    ]

    data_names = [
        'x',
        'y',
        'z',
        'm',
        'h',
        'rho',
        'vx',
        'vy',
        'vz',
        'vxdot',
        'vydot',
        'vzdot',
        'u',
        'udot',
        'grpot',
        'meanmolecular',
        'cc',
        'divv',
        # These are present only when ncooling!=0
        'ueq',
        'tthermal',
    ]

    data_format = [
        'f8', # x
        'f8', # y
        'f8', # z
        'f8', # m
        'f8', # h
        'f8', # rho
        'f8', # vx
        'f8', # vy
        'f8', # vz
        'f8', # vxdot
        'f8', # vydot
        'f8', # vzdot
        'f8', # u
        'f8', # udot
        'f8', # grpot
        'f8', # meanmolecular
        'f4', # cc
        'f8', # divv
        # These are present only when ncooling!=0
        'f8', # ueq
        'f8', # tthermal
    ]

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
    ]

    header_format = '<'+','.join(header_format)

    header_size = sum([header_format.count(str(num))*num for num in range(64)]) + 8 # +8 for newline
    
    with open(filename,'rb') as f:
        f.seek(0,2)
        filesize = f.tell()

    header = FastFileRead(
        filename,
        footer=filesize-header_size,
        binary_format=header_format,
        offset=4,
        parallel=False,
    )[0]

    header.dtype.names = header_names
    if header['ncooling'] == 0:
        data_names = data_names[:-2]
        data_format = data_format[:-2]

    data_format = '<'+','.join(data_format)

    data = FastFileRead(
        filename,
        header=header_size,
        binary_format=data_format,
        offset=4,
        parallel=False,
        verbose=debug > 1,
    )[0]
    data.dtype.names = data_names

    to_return = {
        'data'           : OrderedDict(),
        'display_units'  : OrderedDict(),
        'physical_units' : OrderedDict(),
    }
    for i,dname in enumerate(data_names):
        to_return['data'][dname] = data[dname]
        to_return['display_units'][dname] = display_units[i]
        to_return['physical_units'][dname] = physical_units[i]
    to_return['data']['t'] = header['t'][0]
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
    )[0]

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

