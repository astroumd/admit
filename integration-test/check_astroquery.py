#! /usr/bin/env python
#
from __future__ import print_function
import os, sys

# pip install astroquery
try:
    import astroquery
    print("astroquery OK",astroquery.__version__)
except:
    print("astroquery MISSING")

try:
    from astroquery.alma import Alma
    print("astroquery.alma OK")
except:    
    print("astroquery.alma MISSING")
