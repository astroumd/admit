#! /usr/bin/env python
#
from __future__ import print_function
import os, sys

import numpy

# RuntimeError: module compiled against API version 9 but this version of numpy is 7
# ImportError: numpy.core.multiarray failed to import

# pip install spectral_cube
try:
    import spectral_cube
    print("spectral_cube OK",spectral_cube.__version__)
except:
    print("spectral_cube MISSING")

try:
    import signal_id
    print("signal_id OK",signal_id.__version__)
except:
    print("signal_id MISSING")

try:
    import pvextractor
    print("pvextractor OK",pvextractor.__version__)
except:
    print("pvextractor MISSING")


