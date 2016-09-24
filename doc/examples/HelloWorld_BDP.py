"""Hello World BDP
   ---------------

   This module defines the HelloWorld_BDP class.
"""
from BDP import BDP

class HelloWorld_BDP(BDP):
    """ An example BDP class.

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
        BDP.__init__(self,xmlFile)
        self.yourname = ""
        self.planet = ""
        self.star = ""
        self.setkey(keyval)
