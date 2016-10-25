#! /usr/bin/env python
#
from __future__ import print_function
import os, sys

# pip install astropy
try:
    import astropy
    print("astropy OK",astropy.__version__)
except:
    print("astropy MISSING")

# this seems to fail in CASA, even when astropy is ok ??  (in 0.4.1, is ok in 0.4.2) 
try:
    from astropy.table import Table
    print("astropy.table OK")
except:
    print("astropy.table MISSING")

# pip install astroML
# pip install astroML_addons
try:
    import astroML 
    print("astroML OK",astroML.__version__)
except:
    print("astroML missing")
