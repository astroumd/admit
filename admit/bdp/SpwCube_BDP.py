""" .. _SpwCube-bdp-api:

    **SpwCube_BDP** --- Spectral window cube.
    -----------------------------------------

    This module defines the SpwCube_BDP class.
"""

from Image_BDP import Image_BDP

class SpwCube_BDP(Image_BDP):
    """Generic data cube product.
    
       This class a wrapper around an Image BDP, intended for data cubes.

       Parameters
       ----------
       xmlFile : str
           Output XML file name.
    """
    def __init__(self,xmlFile=None):
        Image_BDP.__init__(self,xmlFile)
        self._version= "0.1.0"
