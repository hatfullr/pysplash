from sys import version_info
if version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import matplotlib
from PIL import Image, ImageTk
from pathlib import Path
import os
import numpy as np
from lib.tkvariable import IntVar


class LinkButton(tk.Checkbutton, object):
    filedirectory = os.path.dirname(os.path.realpath(__file__))
    default_icon_path = os.path.join(filedirectory,"..","images","link.png")
    
    def __init__(self, master, image_file=None, offrelief='flat', overrelief='groove', borderwidth=1, indicatoron=False, **kwargs):
        self.master = master
        self.image_file = image_file
        
        if self.image_file is None:
            mplimagedir = matplotlib.cbook._get_data_path('images')
            self.image_file = os.path.join(mplimagedir, os.path.relpath(LinkButton.default_icon_path, mplimagedir))
            
        super(LinkButton, self).__init__(
            self.master,
            offrelief=offrelief,
            overrelief=overrelief,
            borderwidth=1,
            indicatoron=indicatoron,
            **kwargs
        )
        
        set_image_for_button(self, self.image_file)


# This has been yoinked from the Matplotlib GitHub...
# https://github.com/matplotlib/matplotlib/blob/a6acefea017e378d0e4c6a5793c545caae3a422e/lib/matplotlib/backends/_backend_tk.py
def set_image_for_button(button, imagepath):
    """
    Set the image for a button based on its pixel size.
    The pixel size is determined by the DPI scaling of the window.
    """
    if button.image_file is None:
        return

    # Allow _image_file to be relative to Matplotlib's "images" data
    # directory.
    #path_regular = matplotlib.cbook._get_data_path('images', button.image_file)
    path_regular = Path(imagepath)
    path_large = path_regular.with_name(
        path_regular.name.replace('.png', '_large.png'))
    size = button.winfo_pixels('18p')

    # Nested functions because ToolbarTk calls  _Button.
    def _get_color(color_name):
        # `winfo_rgb` returns an (r, g, b) tuple in the range 0-65535
        return button.winfo_rgb(button.cget(color_name))
    
    def _is_dark(color):
        if isinstance(color, str):
            color = _get_color(color)
        return max(color) < 65535 / 2

    def _recolor_icon(image, color):
        image_data = np.asarray(image).copy()
        black_mask = (image_data[..., :3] == 0).all(axis=-1)
        image_data[black_mask, :3] = color
        return Image.fromarray(image_data, mode="RGBA")

    # Use the high-resolution (48x48 px) icon if it exists and is needed
    with Image.open(path_large if (size > 24 and path_large.exists())
                    else path_regular) as im:
        # assure a RGBA image as foreground color is RGB
        im = im.convert("RGBA")
        image = ImageTk.PhotoImage(im.resize((size, size)), master=button.master)
        button._ntimage = image

        # create a version of the icon with the button's text color
        foreground = (255 / 65535) * np.array(
            button.winfo_rgb(button.cget("foreground")))
        im_alt = _recolor_icon(im, foreground)
        image_alt = ImageTk.PhotoImage(
            im_alt.resize((size, size)), master=button.master)
        button._ntimage_alt = image_alt

    if _is_dark("background"):
        # For Checkbuttons, we need to set `image` and `selectimage` at
        # the same time. Otherwise, when updating the `image` option
        # (such as when changing DPI), if the old `selectimage` has
        # just been overwritten, Tk will throw an error.
        image_kwargs = {"image": image_alt}
    else:
        image_kwargs = {"image": image}
    # Checkbuttons may switch the background to `selectcolor` in the
    # checked state, so check separately which image it needs to use in
    # that state to still ensure enough contrast with the background.
    if (
        isinstance(button, tk.Checkbutton)
        and button.cget("selectcolor") != ""
    ):
        selectcolor = None
        if hasattr(button.master, "_windowingsystem"):
            if button.master._windowingsystem != "x11":
                selectcolor = "selectcolor"
        if selectcolor is None:
            # On X11, selectcolor isn't used directly for indicator-less
            # buttons. See `::tk::CheckEnter` in the Tk button.tcl source
            # code for details.
            r1, g1, b1 = _get_color("selectcolor")
            r2, g2, b2 = _get_color("activebackground")
            selectcolor = ((r1+r2)/2, (g1+g2)/2, (b1+b2)/2)
            
        if _is_dark(selectcolor):
            image_kwargs["selectimage"] = image_alt
        else:
            image_kwargs["selectimage"] = image

    button.configure(**image_kwargs, height='18p', width='18p')
