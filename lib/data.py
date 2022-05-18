import collections
import copy
import numpy as np
import globals
from functions.rotate import rotate

class Data(collections.OrderedDict,object):
    def __init__(self,data,rotations=None,*args,**kwargs):
        if globals.debug > 1: print("data.__init__")
        super(Data,self).__init__(*args,**kwargs)

        for key,val in data.items():
            self[key] = val

        self.is_image = False
            
        dkeys = self.keys()
        if 'image' in dkeys or 'extent' in dkeys:
            if 'image' in dkeys and 'extent' in dkeys:
                self.is_image = True
                return
            else:
                raise ValueError("Must have keys 'image' and 'extent' as keys in the OrderedDict returned by read_file")
        
        # Save the state of the data prior to any modifications
        self._original = copy.deepcopy(data)

        self.display_units = collections.OrderedDict()
        self.physical_units = collections.OrderedDict()
        for key in data['data'].keys():
            self.display_units[key] = data['display_units'][key]
            self.physical_units[key] = data['physical_units'][key]

        if rotations is not None:
            self.rotate(rotations[0],rotations[1],rotations[2])
        
        # Assume linear data initially
        self.scale = 'linear'

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("data.reset")
        if not self.is_image: self.__init__(self._original)

    def rotate(self,anglexdeg,angleydeg,anglezdeg):
        if globals.debug > 1: print("data.rotate")
        if not self.is_image:
            x = self._original['data']['x']
            y = self._original['data']['y']
            z = self._original['data']['z']
            self['data']['x'], self['data']['y'], self['data']['z'] = rotate(x,y,z,anglexdeg,angleydeg,anglezdeg)

