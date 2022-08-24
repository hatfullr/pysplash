# Compact support of the kernel function defined in
# kernel.py
compact_support = 2.

# Various debugging levels, for granular control on
# verbosity in the code. Higher values of debug mean
# more information will be printed to the terminal.
# Set this to 0 to get no output to the terminal at
# all.
debug = 0

# In some cases you might get a performance boost if
# you allow the use of multiprocessing. It depends
# on a few factors, one of which is the hardware
# that is being used. On my hardware, setting this
# value to False gives ~10x performance increase.
use_multiprocessing_on_scatter_plots = False

# The width of a tooltip to determine text wrapping
tooltip_wraplength = 50

# When interacting with the plot by panning or
# zooming using the mouse, this parameter is used to
# determine how long in miliseconds after the change
# in the plot to wait before calculating the new
# image. Lower values decrease performance but make
# the application feel more responsive.
plot_update_delay = 10

# The minimum allowed point size
point_size_minimum = 0.5

# When using hotkeys to rotate the plot, this is the
# default increment/decrement amount in degrees.
rotation_step = 15

# When using math expressions in the axis controllers
# such as "x * x", you can import installed Python
# modules for use by adding the import statement to
# this variable.
exec_imports = [
    "import matplotlib",
    "import numpy as np",
]

# Specify the location of the profile directory
import os.path
profile_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"profile")

# When click-dragging with the mouse on the plot, this
# determines the minimum allowed size of the selection
minimum_selection_size = 5





# Internal use variables. Only edit these variables
# if you really know what you are doing.
hotkey_pressed = False

# allow starting in time mode if True. Also used to
# control time mode at runtime
time_mode = False

def init():
    global state_variables
    state_variables = []
