import sys
if sys.version_info.major < 3:
    from integratedvalueplot import IntegratedValuePlot
else:
    from lib.integratedvalueplot import IntegratedValuePlot

import numpy as np
import math
import kernel
import globals
if globals.debug > 0: from time import time

try:
    from numba import cuda
    has_jit = True
except ImportError:
    has_jit = False


# 'attenuator' is either the opacity or the optical depth,
# and real_mode is either 'opacity' or 'tau'
    
class RealPlot(IntegratedValuePlot, object):
    def __init__(self, attenuator, real_mode, *args, **kwargs):
        self.attenuator = np.ascontiguousarray(attenuator, dtype=np.double)
        self.real_mode = real_mode
        super(RealPlot, self).__init__(*args, **kwargs)

        if self.real_mode == 'opacity':
            taus = self.attenuator * self.rho * 2*self.h
            self.quantity *= np.exp(-taus) * self.attenuator * self.rho
        elif self.real_mode == 'tau':
            kappas = self.attenuator * self.rho / (2*self.h)
            self.quantity *= np.exp(-self.attenuator) * kappas * self.rho
        else:
            raise ValueError("unrecognized value for real_mode '"+str(self.real_mode)+"'. Must be either 'opacity' or 'tau'")
        
