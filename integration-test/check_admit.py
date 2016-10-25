#! /usr/bin/env python
#
from __future__ import print_function
import os, sys


try:
    import admit
    print("admit OK",admit.__version__)
except:
    print("admit MISSING")

