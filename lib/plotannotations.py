from functions.setpreference import set_preference
from functions.getpreference import get_preference
import matplotlib
import globals
#import numpy as np

class PlotAnnotations(dict, object):
    def __init__(self,ax):
        if globals.debug > 1: print("plotannotations.__init__")
        
        self.ax = ax
        self.master = self.ax.get_figure().canvas.get_tk_widget()
        
        self._kwargs = {}

        # Load the preferences
        
        save_object = get_preference(self.master, "annotations")
        initial = {}
        if save_object is not None:
            for key, obj in save_object.items():
                if 'text' in obj['kwargs'].keys(): obj['kwargs'].pop('text')
                initial[key] = self.ax.annotate(obj['text'],obj['position'],**obj['kwargs'])
                self._kwargs[key] = obj['kwargs']

        super(PlotAnnotations, self).__init__(initial)
        self.master.bind("<<BeforePreferencesSaved>>", self.save, add="+")
        self.master.bind("<<ArtistRemoved>>", self.on_artist_removed, add="+")

    def pop(self, *args, **kwargs):
        if globals.debug > 1: print("plotannotations.pop")
        self._kwargs.pop(*args, **kwargs)
        return super(PlotAnnotations,self).pop(*args,**kwargs)

    def save(self, *args, **kwargs):
        if globals.debug > 1: print("plotannotations.save")

        save_object = {}
        for ID, annotation in self.items():
            save_object[ID] = {
                'text' : annotation.get_text(),
                'position' : annotation.get_position(),
                'kwargs' : self._kwargs[ID],
            }
        
        set_preference(self.master, "annotations", save_object)

    def add(self, key, *args, **kwargs):
        if globals.debug > 1: print("plotannotations.add")
        if 'text' in kwargs.keys(): kwargs.pop('text')
        self[key] = self.ax.annotate(*args, **kwargs)
        self._kwargs[key] = kwargs
        return self[key]

    def remove(self, key, *args, **kwargs):
        if globals.debug > 1: print("plotannotations.remove")
        self[key].remove()
        self.pop(key)

    def configure(self, key, **kwargs):
        if globals.debug > 1: print("plotannotations.configure")
        self[key].set(**kwargs)
        for k, val in kwargs.items():
            self._kwargs[key][k] = val
            
    # When an artist gets removed, search to see if it was one of our artists
    def on_artist_removed(self, *args, **kwargs):
        if globals.debug > 1: print("plotannotations.on_artist_removed")
        removed_keys = []
        for key,artist in self.items():
            if artist.get_figure() is None: removed_keys.append(key)
        for key in removed_keys: self.pop(key)

    # Remove and re-add all the annotations
    def reload(self, which=None):
        if globals.debug > 1: print("plotannotations.reload")

        if which is None: which = self.keys()
        renderer = self.ax.get_figure().canvas.get_renderer()
        for key, artist in self.items():
            if key in which:
                position = artist.get_position()
                text = artist.get_text()
                artist.remove()
                self.add(key, text, position, **self._kwargs[key])
        self.ax.get_figure().canvas.draw_idle()
        self.ax.get_figure().canvas.flush_events()
    
