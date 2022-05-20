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

# When using math expressions in the axis controllers
# such as "x * x", you can import installed Python
# modules for use by adding the import statement to
# this variable.
exec_imports = [
    "import numpy as np",
]









# Internal use variables. Only edit these variables
# if you really know what you are doing.
hotkey_pressed = False

def init():
    global state_variables
    state_variables = []
