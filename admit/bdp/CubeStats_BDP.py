""" .. _CubeStats-bdp-api:

    **CubeStats_BDP** --- Plane-based cube statistics.
    --------------------------------------------------

    This module defines the CubeStats_BDP class.
"""
import admit.util.bdp_types as bt
from Table_BDP import Table_BDP
from Image_BDP import Image_BDP

class CubeStats_BDP(Table_BDP,Image_BDP):
    """Holds the plane based statistics of a cube

    See CubeStats_AT as an example that computes this table.

    Attributes
    ----------

    mean : real

    sigma : real

    robust : list

    maxval : real

    maxpos : array (of length 3)

    minval : real

    minpos : array (of length 3)

    """
    def __init__(self,xmlFile=None,**keyval):
        Table_BDP.__init__(self,xmlFile)    # the Table
        Image_BDP.__init__(self,xmlFile)    # some helpful pictures
        self.mean   = 0.0
        self.sigma  = 0.0
        self.minval = 0.0
        self.maxval = 0.0
        self.minpos = []
        self.maxpos = []
        self.robust = []
        self.setkey(keyval)
        self._version= "0.2.0"

    def _show(self):
        # the baseclass show() should do it
        print "# mean:",self.mean
        print "# sigma:",self.sigma
        print "# maxval:",self.maxval
        print "# maxpos:",self.maxpos
        print "# robust:",self.robust
