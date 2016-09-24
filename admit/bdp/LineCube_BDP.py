""" **LineCube_BDP** --- LineCube_AT data (cube and line information).
    ------------------------------------------------------------------

    This module defines the BDP to hold LineCubes.
"""

from Line_BDP import Line_BDP
from Image_BDP import Image_BDP


class LineCube_BDP(Line_BDP, Image_BDP):
    """ Class for holding LineCube data.

        This class holds both a spectral cube and line information of a
        specific spectral line.

        Parameters
        ----------
        xmlFile : str
            Output XML file name.

        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        image : Image
            Instance of the Image class to hold the spectral cube.

        line : Line
            Instance of the Line class to hold an information on the spectral
            line.

        linewidth : float
            The width of the spectral line, in km/s.

        linechans : string
            The start and end channels in the linecube that actually comprise
            the line. Example "10~20", which would be channels 10 through
 	    (and including) 20. These are channel numbers based on this cube,
            not the original spectral window cube or where ever it was derived
            from.
    """
    def __init__(self, xmlFile=None, **keyval):
        Image_BDP.__init__(self, xmlFile)
        Line_BDP.__init__(self, xmlFile)
        self.linewidth = 0.0
        self.linechans = ""
        self.setkey(keyval)
        self._version= "0.1.0"
