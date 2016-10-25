#! /usr/bin/env python
#
from __future__ import print_function
import os, sys


try:
    import numpy
    print("numpy OK",numpy.__version__)
except:
    print("numpy MISSING")

try:
    import scipy
    print("scipy OK",scipy.__version__)
except:
    print("scipy MISSING")

try:
    import matplotlib
    print("matplotlib OK",matplotlib.__version__)
except:
    print("matplotlib MISSING")


try:
    import sklearn
    print("sklearn OK",sklearn.__version__)
except:
    print("sklearn MISSING")

try:
    import statsmodels
    print("statsmodels OK",statsmodels.__version__)
except:
    print("statsmodels MISSING")


try:
    import rpy2
    print("rpy2 OK",rpy2.__version__)
except:
    print("rpy2 MISSING")


try:
    import pandas
    print("pandas OK",pandas.__version__)
except:
    print("pandas MISSING")

