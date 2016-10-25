#! /usr/bin/env python
#
from __future__ import print_function
import os, sys

import numpy

# RuntimeError: module compiled against API version 9 but this version of numpy is 7
# ImportError: numpy.core.multiarray failed to import

try:
    import aplpy
    print("aplpy OK",aplpy.__version__)
except:
    print("aplpy MISSING")
    sys.exit(0)
 
