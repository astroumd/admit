""" .. _CubeSpectrum-bdp-api:

   **CubeSpectrum_BDP** --- Data cube spectra.
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   
   This module defines the CubeSpectrum_BDP class.
"""
from Table_BDP import Table_BDP
from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

class CubeSpectrum_BDP(Table_BDP,Image_BDP):
    """ Contains (one or more) spectra from a cube.

    See CubeSpectrum_AT as an example that computes this kind of table.
    """
    def __init__(self,xmlFile=None,**keyval):
        Table_BDP.__init__(self,xmlFile)
        Image_BDP.__init__(self,xmlFile)
        self.mean  = 0.0
        self.sigma = 0.0
        self.setkey(keyval)
        self._version= "0.1.0"
