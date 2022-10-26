# When True, the threading module will be used to
# split large tasks out to multiple threads to
# improve performance. You can try setting this to
# False if you are experiencing errors.
support_threading = True

# For GPU-enabled calculations, use this many threads
# per compute block. The number of threads you can
# or should use depends on your hardware. There is
# unfortunately no way to calculate a proper value,
# as GPU hardware architecture changes all the time.
threadsperblock = 512

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
use_multiprocessing = False

# When in Time Mode we create "point density" plots
# with time on the x-axis. In this way, all the files
# imported into PySplash are shown. However, if there
# are many files imported then the RAM limit might be
# reached. Thus, we create the "point density" plots
# by reading in this number of files at a time and
# plotting them in groups.
time_mode_nfiles = 5

# The width of a tooltip to determine text wrapping
tooltip_wraplength = 50

# When interacting with the plot by panning or
# zooming using the mouse, this parameter is used to
# determine how long in miliseconds after the change
# in the plot to wait before calculating the new
# image. Lower values decrease performance and
# higher values put a hard limit on the fps.
# Adjusting this can significantly impact performance.
plot_update_delay = 100

# These will be overridden by the user's preferences
# if those preferences have been set.
default_particle_color = [0.,0.,0.,1.] # black
neighbor_particle_color = [1.,0.,0.,1.] # red

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

# Never edit this
threaded_tasks = []

# Never edit this value in this file.
gpu_busy = False

def init():
    global state_variables
    state_variables = []
