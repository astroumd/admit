"""
   .. _PVCorr-bdp-api:

   **PVCorr_BDP** --- PVCorr_AT data (image and table).
   ----------------------------------------------------

   This module defines the PVCorr_BDP class.
"""


from Image_BDP import Image_BDP
from Table_BDP import Table_BDP
#import admit.util.bdp_types as bt

class PVCorr_BDP(Table_BDP, Image_BDP):
    """ PVCorr Basic Data Product.

    """
    def __init__(self,xmlFile=None,**keyval):
        Table_BDP.__init__(self,xmlFile)
        Image_BDP.__init__(self,xmlFile)
        self.sigma = 0.0
        self.setkey(keyval)
        self._version= "0.1.0"
