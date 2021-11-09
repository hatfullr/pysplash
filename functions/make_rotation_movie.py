from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
from matplotlib.animation import FuncAnimation
import numpy as np

def make_rotation_movie(gui):
    nframes = 90+90
    
    def update(i):
        if gui.controls.rotation_x.get() != 90:
            gui.controls.rotation_x.set(gui.controls.rotation_x.get() + 1)
        elif gui.controls.rotation_z.get() != 90:
            gui.controls.rotation_z.set(gui.controls.rotation_z.get() + 1)
        gui.do_rotation(redraw=True)

        if ((int(gui.controls.rotation_x.get())%10 == 0 and gui.controls.rotation_z.get() == 0) or
            (int(gui.controls.rotation_z.get())%10 == 0 and gui.controls.rotation_x.get() == 90)):
            progress = int(float(i)/float(nframes) * 100)
            gui.message("Creating rotations movie... (%d%%)" % (progress))
            gui.update_idletasks()
        if i == nframes-1:
            gui.message("Saving rotations movie...")
            gui.update_idletasks()
        return gui.interactiveplot.drawn_object,
    
    savefile = tk.filedialog.asksaveasfilename()
    if not savefile: return
    
    gui.message("Creating rotations movie...")
    gui.set_user_controlled(False)
    
    anim = FuncAnimation(
        gui.interactiveplot.fig,
        update,
        init_func=gui.reset_rotation(redraw=True),
        frames=nframes,
        interval=50,
        blit=True,
    )
    
    anim.save(savefile)
    gui.clear_message()
    
    gui.set_user_controlled(True)
    

