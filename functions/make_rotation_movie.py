from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from matplotlib.animation import FuncAnimation
import numpy as np
from functions.rotate import rotate

def make_rotation_movie(gui):
    nframes = 90+90+1

    def update(i):

        if i <= 90:
            anglex = i
            anglez = 0
        else:
            anglex = 90
            anglez = i-90
        
        #anglex = gui.controls.rotation_x.get() + 1
        #anglez = gui.controls.rotation_z.get() + 1
        if gui.controls.rotation_x.get() != 90:
            gui.controls.rotation_x.set(anglex)
        elif gui.controls.rotation_z.get() != 90:
            gui.controls.rotation_z.set(anglez)

        print(i,nframes,anglex,anglez)
        gui.data.rotate(anglex,0,anglez)
        gui.interactiveplot.update()

        if ((anglex%10 == 0 and anglez == 0) or
            (anglex == 90 and anglez%10 == 0)):
            progress = int(float(i)/float(nframes) * 100)
            gui.message("Creating rotations movie... (%d%%)" % (progress))
            gui.update()
        if i == nframes-1:
            gui.message("Saving rotations movie...")
            gui.update()
        return gui.interactiveplot.drawn_object,
    
    savefile = tk.filedialog.asksaveasfilename()
    if not savefile: return
    
    gui.message("Creating rotations movie...")
    gui.set_user_controlled(False)
    
    anim = FuncAnimation(
        gui.interactiveplot.fig,
        update,
        #init_func=gui.interactiveplot.reset_rotation(redraw=True),
        frames=nframes,
        interval=50,
        blit=True,
    )
    
    anim.save(savefile)
    gui.clear_message()
    
    gui.set_user_controlled(True)
    

