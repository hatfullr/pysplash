import collections
import copy
import numpy as np
import globals
from functions.rotate import rotate

class Data(collections.OrderedDict,object):
    def __init__(self,data):
        if globals.debug > 1: print("data.__init__")
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

    def reset(self,*args,**kwargs):
        if globals.debug > 1: print("data.reset")
        if not self.is_image: self.__init__(self._original)

    def mask(self, mask):
        if globals.debug > 1: print("data.mask")
        pass

    # Mask the original data by a radial slice, so that particles who are
    # located within the slice are shown, and those outside are hidden
    def radial_mask(self, rmin, rmax, origin=np.zeros(3)):
        if globals.debug > 1: print("data.radial_mask")
        if isinstance(origin, int): origin = xyz[origin]
        xyz = np.column_stack((
            self._original['data']['x'],
            self._original['data']['y'],
            self._original['data']['z'],
        ))
        r2 = np.sum((xyz-origin)**2, axis=-1)
        self.mask(np.logical_and(rmin*rmin <= r2, r2 <= rmax*rmax))

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

