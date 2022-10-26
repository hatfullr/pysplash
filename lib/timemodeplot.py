import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from lib.customaxesimage import CustomAxesImage
from lib.data import Data
import numpy as np
import matplotlib.collections
import matplotlib.image

import globals
from read_file import read_file
from copy import copy
from time import time
import collections

try:
    from numba import cuda
    import math
    has_jit = True
except ImportError:
    has_jit = False

# Here yname is the name of the column to plot. We read in
# groups of files using read_file and populate the plot
# iteratively. The x-axis will always be time.

class TimeModePlot(CustomAxesImage, object):
    def __init__(self, ax, gui, **kwargs):
        if globals.debug > 1: print("timemodeplot.__init__")

        self.ax = ax
        self.gui = gui
        
        if not self.gui.time_mode.get():
            raise Exception("cannot create a TimeModePlot when not in Time Mode")

        self.filenames = np.array(copy(self.gui.filenames), dtype=str)
        kwargs['resolution_steps'] = tuple([1])

        if 'cmap' not in kwargs.keys():
            colorbar = kwargs.get('colorbar', None)
            if colorbar is not None:
                kwargs['cmap'] = colorbar.cmap

        self.groupsize = max(int(len(self.filenames)/float(globals.time_mode_nfiles)), 1)
        self.group_idx = np.array_split(np.arange(len(self.filenames)), self.groupsize)
        self.group_filenames = np.array_split(self.filenames, self.groupsize)
        
        
        super(TimeModePlot, self).__init__(
            ax,
            np.full((1,1),0.),
            **kwargs
        )

        self.images = []
        interpolation = self.get_interpolation()
        for i in range(len(self.group_filenames)):
            image = matplotlib.image.AxesImage(
                self.ax,
                interpolation=interpolation,
                **self.kwargs,
            )
            self.images.append(image)
            self.ax.add_image(image)

        if self.colorbar is not None:
            self.colorbar.disconnect_axesimage(self)
            for image in self.images:
                self.colorbar.connect_axesimage(image)
            self.colorbar.show()

    def get_data(self, filenames):
        if globals.debug > 1: print("timemodeplot.get_data")

        xstring = self.gui.controls.axis_controllers['XAxis'].value.get()
        ystring = self.gui.controls.axis_controllers['YAxis'].value.get()
        
        data = {
            'data' : collections.OrderedDict({}),
            'display_units' : collections.OrderedDict({}),
            'physical_units' : collections.OrderedDict({}),
        }

        compact_support = None
        datalength = None
        for filename in filenames:
            d = read_file(filename)

            # Check for inconsistent data
            if compact_support is None:
                compact_support = d.get('compact_support',None)
            else:
                if 'compact_support' in d.keys():
                    if d['compact_support'] != compact_support:
                        raise ValueError("compact_support value mismatch")
                else:
                    raise ValueError("compact_support value mismatch")

            length = 0
            for key,val in d['data'].items():
                if key not in ['t','time','Time']:
                    length = len(val)
                    break
            if length == 0: raise Exception("data file '"+filename+"' either only contains time data, or has no data at all")

            for key, val in d['data'].items():
                if key not in xstring and key not in ystring: continue
                if key in ['t','time','Time']: val = np.repeat(val, length)
                if key not in data['data'].keys(): data['data'][key] = [val]
                else: data['data'][key] += [val]

                if key not in data['display_units'].keys():
                    data['display_units'][key] = d['display_units'][key]
                elif data['display_units'][key] != d['display_units'][key]:
                    raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found display units of '"+data['display_units'][key]+"', but file '"+filename+"' has display units of '"+d['display_units'][key]+"' for this key.")

                if key not in data['physical_units'].keys():
                    data['physical_units'][key] = d['physical_units'][key]
                elif data['physical_units'][key] != d['physical_units'][key]:
                    raise Exception("the input files have inconsistent data structures. For key '"+key+"', we previously found physical units of '"+data['display_units'][key]+"', but file '"+filename+"' has physical units of '"+d['display_units'][key]+"' for this key.")

        for key, val in data['data'].items():
            data['data'][key] = np.array(val).flatten()
        self.gui.data = data

        self.gui.controls.axis_controllers['XAxis'].stale = True
        self.gui.controls.axis_controllers['YAxis'].stale = True

        
    def calculate(self, *args, **kwargs):
        if globals.debug > 1: print("timemodeplot.calculate")
        if globals.debug > 0: start = time()

        # Remove the interactive plot's currently drawn object
        for child in self.ax.get_children():
            if isinstance(child, CustomAxesImage) and child is not self:
                child.remove()
        
        canvas = self.ax.get_figure().canvas
        group_xpixels = np.array_split(np.arange(len(self.filenames)), self.groupsize)

        for image in self.images: image.set_data(np.full((1,1),np.nan))
        
        new_max = None
        new_data = []
        
        for i,(image,idx,group,xpixels) in enumerate(zip(self.images, self.group_idx, self.group_filenames, group_xpixels)):
            if self._interrupt: return
            self.get_data(group)
            time = self.gui.controls.axis_controllers['XAxis'].data
            y = self.gui.controls.axis_controllers['YAxis'].data

            valid = np.logical_and(np.isfinite(time), np.isfinite(y))

            if not np.any(valid):
                image.remove()
                continue
            
            time = time[valid]
            y = y[valid]

            unique_time = np.unique(time)
            xbins = np.empty(len(unique_time)+1)
            xbins[:-1] = unique_time
            # This is sort-of a guess at the duration of the last time step. We don't ask for dt
            # information so we have to extrapolate.
            xbins[-1] = unique_time[-1]+(unique_time[-1]-unique_time[-2])

            if self._interrupt: return
            pixels, extent = self.calculate_data_cpu(time, y, xbins)

            new_data.append(pixels)
            
            if new_max is None: new_max = np.nanmax(pixels)
            else: new_max = max(new_max, np.nanmax(pixels))

            if self._interrupt: return

            for j,dat in enumerate(new_data):
                self.images[j].set_data(dat / new_max)
            
            image.set_extent(extent)
            canvas.draw_idle()

        self.gui.data = None
            
        if globals.debug > 0: print("timemodeplot.calculate took %f seconds" % (time()-start))

    def calculate_data_cpu(self, x, y, xbins):
        if globals.debug > 1: print("timemodeplot.calculate_data_cpu")
        ybins = np.linspace(np.nanmin(y), np.nanmax(y), self.ypixels+1)
        pixels, yedges, xedges = np.histogram2d(
            y,x,
            bins=[ybins,xbins],
        )
        
        # This step ensures that the bins appear centered
        dx = xedges[1]-xedges[0]
        dy = yedges[1]-yedges[0]
        extent = np.array([
            np.amin(xedges),
            np.amax(xedges),
            np.amin(yedges),
            np.amax(yedges),
        ])
        
        pixels[pixels == 0] = np.nan
        return pixels, extent
    
    def remove(self,*args,**kwargs):
        if globals.debug > 1: print("timemodeplot.remove")
        if self.colorbar is not None:
            for image in self.images:
                self.colorbar.disconnect_axesimage(image)
        for artist in self.ax.get_children():
            if artist in self.images:
                artist.remove()
                self.images.remove(artist)
        #for image in self.images: image.remove()

    def set_data(self, *args, **kwargs):
        if globals.debug > 1: print("timemodeplot.set_data")
        raise Exception("set_data cannot be called on a TimeModePlot")

    def _after_calculate(self, *args, **kwargs):
        if globals.debug > 1: print("timemodeplot._after_calculate")
        self.thread = None
        self.after_calculate()
        if self.aftercalculate is not None:
            self.aftercalculate(*args, **kwargs)
        if self.resolution_step == self.resolution_steps[-1]:
            self.calculating = False
