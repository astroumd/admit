"""Hello World Inherit BDP
   -----------------------

   This module defines the HelloWorld_Inherit_BDP class.
"""
from admit.bdp.Image_BDP import Image_BDP
from admit.bdp.Table_BDP import Table_BDP

class HelloWorld_Inherit_BDP(Image_BDP,Table_BDP):
    """ An example BDP class. Inherits from Image_BDP and Table_BDP.

        Parameters
        ----------
        xmlFile : string, optional
            Basename of the file where the BDP data will be stored on write

        Attributes
        ----------
        yourname : string
            The name of the person in the BDP

        planet : string
            Then name of the home planet

        star : string
            The name of the home star

    """
    def __init__(self,xmlFile=None,**keyval):
        Image_BDP.__init__(self,xmlFile)
        Table_BDP.__init__(self,xmlFile)
        self.yourname = ""
        self.planet = ""
        self.star = ""
        self.setkey(keyval)
