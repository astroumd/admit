"""
   .. _PVSlice-bdp-api:

   **PVSlice_BDP** --- PVSlice_AT data (image).
   --------------------------------------------

   This module defines the PVSlice_BDP class.
"""

from Image_BDP import Image_BDP
import admit.util.bdp_types as bt

#@ todo   This used to be LineImage, instead of Image.  

class PVSlice_BDP(Image_BDP):
    """ PVSlice Basic Data Product

        PVSlice taken from an Image cube.

        Parameters
        ----------
        xmlFile : string
            Output XML file name.

        keyval : dictionary
            Dictionary of keyword value pairs.

        Attributes
        ----------
        image : Image
            An Image class to hold the PVSlice data.

        line : string
            String describing the line in the cube. Usually 4 numbers.

        method : string
            Method describing the line. Possible are 'slice' and 'slit'.
    """
    def __init__(self,xmlFile=None,**keyval):
        Image_BDP.__init__(self,xmlFile)
        self.mean   = 0.0
        self.sigma  = 0.0
        self.line   = ""
        self.method = ""
        self.setkey(keyval)
        self._version= "0.1.0"
