import collections
import copy
import numpy as np
import globals

runit = 6.599e10
munit = 1.9891e33

class Data(collections.OrderedDict,object):
    def __init__(self,data,rotations=None,*args,**kwargs):
        if globals.debug > 1: print("data.__init__")
        super(Data,self).__init__(*args,**kwargs)

        for key,val in data.items():
            self[key] = val
        
        # Save the state of the data prior to any modifications
        self._original = copy.deepcopy(data)

        self.display_units = collections.OrderedDict()
        self.physical_units = collections.OrderedDict()
        for key in data['data'].keys():
            self.display_units[key] = data['display_units'][key]
            self.physical_units[key] = data['physical_units'][key]

        if rotations is not None:
            self.rotate(rotations[0],rotations[1],rotations[2])
        
    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("data.reset")
        self.__init__(self._original)
        
    def rotate(self,anglexdeg,angleydeg,anglezdeg):
        if globals.debug > 1: print("data.rotate")
        xangle = float(anglexdeg)/180.*np.pi
        yangle = float(angleydeg)/180.*np.pi
        zangle = float(anglezdeg)/180.*np.pi

        x = self._original['data']['x']
        y = self._original['data']['y']
        z = self._original['data']['z']
        
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
            
        self['data']['x'] = x
        self['data']['y'] = y
        self['data']['z'] = z

