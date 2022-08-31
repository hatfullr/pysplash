from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class CustomCanvas(FigureCanvasTkAgg, object):
    def __init__(self, *args, **kwargs):
        self.blit_artists = kwargs.pop('blit_artists', [])
        super(CustomCanvas,self).__init__(*args,**kwargs)

        self._background = None
        self.draw()
        
        # Get the initial background
        #self._background = None
        #self.get_background(None)

        # Grab the background on every draw
        #self.cid = self.mpl_connect("draw_event", self.get_background)


    def get_background(self, event):
        if event is not None:
            if event.canvas != self:
                raise RuntimeError("canvas mismatch")
        self._background = self.copy_from_bbox(self.figure.bbox)

    def draw(self,*args,**kwargs):
        #return
        #self.get_background(None)
        return super(CustomCanvas,self).draw(*args,**kwargs)
        
    def draw_idle(self,*args,**kwargs):
        #return
        """
        bg = self.copy_from_bbox(self.figure.bbox)
        self.restore_region(bg)

        for ax in np.array(self.figure.axes).flatten():
            for artist in ax.get_children():
                ax.draw_artist(artist)
        
        self.blit(self.figure.bbox)
        self.flush_events()
        """

        try:
            if self._background is None: self.get_background(None)
            else:
                self.restore_region(self._background)
                for artist in self.blit_artists:
                    self.figure.draw_artist(artist)
                self.blit(self.figure.bbox)
            self.flush_events()
        except AttributeError as e:
            if str(e) == 'draw_artist can only be used after an initial draw which caches the renderer':
                self.draw(*args,**kwargs)
            else: raise(e)
        
