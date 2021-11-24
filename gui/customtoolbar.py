from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
from matplotlib.collections import PathCollection
import numpy as np
import sys

class CustomToolbar(NavigationToolbar2Tk):
    def __init__(self,master,gui,canvas,**kwargs):
        self.toolitems = (
            (u'Home', u'', u'home', u'home'),
            (u'Pan', u'', u'move', u'pan'),
            (u'Zoom', u'', u'zoom_to_rect', u'zoom'),
            (u'Subplots', u'', u'subplots', u'configure_subplots'),
            (u'Save', u'', u'filesave', u'save_figure'),
            )
        self.master = master
        self.gui = gui
        self.canvas = canvas
        self.toolbar = NavigationToolbar2Tk
        self.toolbar._old_Button = self.toolbar._Button
        self.toolbar._Button = self._new_Button
        self.toolbar.__init__(self,self.canvas,self.master)
        #self.toolbar.home = self.new_home

        self.queued_zoom = None
        
        self.configure(**kwargs)

        # Remove the "x=... y=..." labels
        for child in self.children:
            if type(child).__name__ == 'Label':
                child.pack_forget()

    def home(self,*args,**kwargs):
        self.gui.interactiveplot.reset_data_xylim()
                
    def _new_Button(self, *args, **kwargs):
        b = self._old_Button(*args, **kwargs)
        # It expects dpi=100, but we have a different dpi. Because shit is
        # stupid, we have to first increase the image size then decrease it
        # using integers.
        b._ntimage = b._ntimage.zoom(self.canvas.figure.dpi,self.canvas.figure.dpi)
        b._ntimage = b._ntimage.subsample(100,100)
        self.height = b._ntimage.height()
        b.config(height=self.height,image=b._ntimage)
        return b


    def on_queued_zoom(self,event):
        flag = False
        if self.gui.interactiveplot.drawn_object is not None: flag = True

        if flag: self.gui.interactiveplot.drawn_object._disconnect()
            
        super(CustomToolbar,self).release_zoom(event)

        if flag: self.gui.interactiveplot.drawn_object._connect()
    
    def release_zoom(self,event):
        self.queued_zoom = None
        if sys.version_info.major < 3: # Python2
            for zoom_id in self._ids_zoom:
                self.canvas.mpl_disconnect(zoom_id)
            self.queued_zoom = lambda event=event: self.on_queued_zoom(event)
        else: # Python3
            if self._zoom_info is not None:
                if isinstance(self._zoom_info,dict):
                    axes = self._zoom_info['axes']
                    cid = self._zoom_info['cid']
                elif hasattr(self._zoom_info,'axes'):
                    axes = self._zoom_info.axes
                    cid = self._zoom_info.cid
                else:
                    raise ValueError("Problem with the matplotlib zoom function. Please submit a bug report on GitHub with your current version of matplotlib.")
                self.canvas.mpl_disconnect(cid)
                self.queued_zoom = lambda event=event: self.on_queued_zoom(event)
        if self.queued_zoom is not None:
            self.gui.controls.save_state()
            self.gui.controls.on_state_change()


