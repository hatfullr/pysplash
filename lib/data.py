import collections
import copy
import numpy as np
import globals
from functions.rotate import rotate
import kernel

class Data(collections.OrderedDict,object):
    def __init__(self,data,mask=None):
        if globals.debug > 1: print("data.__init__")
        kernel.compact_support = data.pop('compact_support',kernel.compact_support)
        super(Data,self).__init__(data)

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

        self.rotation = np.zeros(3) # Euler angles

        self._mask = mask
        if mask is not None: self.mask(self._mask)

    @property
    def n(self):
        for name,column in self['data'].items():
            if name not in ['t','time']:
                return len(column)
        return 0

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("data.reset")
        if not self.is_image: self.__init__(self._original,**kwargs)

    def clear_mask(self, *args, **kwargs):
        if globals.debug > 1: print("data.clear_mask")
        rotation = copy.deepcopy(self.rotation) # Copy just to be safe
        self.reset()
        self.rotate(*rotation)
        self._mask = None
        
    # Use None for mask to clear the mask
    def mask(self, mask):
        if globals.debug > 1: print("data.mask")

        for key, val in self['data'].items():
            if key in ['t','time'] and not globals.time_mode: continue
            self['data'][key] = val[mask]
        self._mask = mask

    # Rotate the data using euler angles
    def rotate(self, anglexdeg, angleydeg, anglezdeg):
        if globals.debug > 1: print("data.rotate")
        if self.is_image:
            raise Exception("cannot perform rotations on data that have been identified as an image with is_image = True.")

        xyzangledeg = np.array([anglexdeg,angleydeg,anglezdeg],dtype=float)
        dangle = xyzangledeg - self.rotation
        self.rotation = xyzangledeg
        xyzangledeg = -dangle

        self['data']['x'], self['data']['y'], self['data']['z'] = rotate(
            self['data']['x'],
            self['data']['y'],
            self['data']['z'],
            xyzangledeg[0],
            xyzangledeg[1],
            xyzangledeg[2],
        )

