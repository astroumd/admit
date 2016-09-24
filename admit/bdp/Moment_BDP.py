"""
    .. _Moment-BDP-api:

    **Moment_BDP** --- Moment_AT data (images and line information).
    ----------------------------------------------------------------

    This module defines the Moment_BDP class.
"""
from Image_BDP import Image_BDP
from Line_BDP import Line_BDP


class Moment_BDP(Image_BDP, Line_BDP):
    """ Moment_BDP class.

        Class for holding the data (images and line info) for a moment.

        Parameters
        ----------
        xmlFile : str
            Output XML file name.

        keyval : dict
            Dictionary of keyword : value pairs.

        Attributes
        ----------
        moment : int
            The moment that this BDP holds.

        line : Line
            Instance of Line class to hold any information on the spectral line
            contained in the moment.

        image : Image
            Instance of MultiImage class which holds the moment image,
            histogram, and any other representations of the data.

    """
    def __init__(self, xmlFile=None, **keyval):
        Image_BDP.__init__(self, xmlFile)
        Line_BDP.__init__(self, xmlFile)
        self.moment = 0
        self.setkey(keyval)
        self._version= "0.1.0"
