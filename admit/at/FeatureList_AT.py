""" .. _FeatureList-at-api:

   **FeatureList_AT** --- Finds "features" in a (continuum) map.
   -------------------------------------------------------------

   This module defines the FeatureList_AT class.
"""
import sys, os

from admit.AT import AT
import admit.util.bdp_types as bt
from admit.util.Image import Image
from admit.util.utils import Dtime
from admit.bdp.CubeStats_BDP import CubeStats_BDP
from admit.bdp.Image_BDP import Image_BDP

import numpy as np
try:
  import taskinit
  import casa
except:
  print "WARNING: No CASA; FeatureList task cannot function."

class FeatureList_AT(AT):
    """Find features in a map.

    This is a placeholder.
    For now, only continuum maps are handled. 

    """
    def __init__(self,**keyval):
        keys = {
               }
        AT.__init__(self,keys,keyval)
        self._version = "0.0.1"
        self.set_bdp_in([(Image_BDP,1,bt.REQUIRED),
                         (CubeStats_BDP,1,bt.OPTIONAL)])
        self.set_bdp_out([])
    def run(self):

        dt = Dtime()

        dt.tag("done")
        dt.end()
