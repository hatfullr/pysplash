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

        x = copy.copy(self._original['data']['x'])
        y = copy.copy(self._original['data']['y'])
        z = copy.copy(self._original['data']['z'])
        
        self['data']['x'], self['data']['y'], self['data']['z'] = rotate(x,y,z,anglexdeg,angleydeg,anglezdeg)
