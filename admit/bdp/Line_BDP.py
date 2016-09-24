"""
   .. _Line-bdp-api:

   **Line_BDP** --- Line data base.
   --------------------------------

   This module defines the Line_BDP class.
"""
# get the main BDP base class
from BDP import BDP

# get the line base class
from admit.util.Line import Line


# set up the inheritance
class Line_BDP(BDP):
    """
        Line base class for use in BDP's. BDP's that contain transition
        information should inherit from this class. In the instance
        where line data for more than one transition is needed then
        the class should instantiate instances of the Line class
        directly.

        Parameters
        ----------
        xmlFile : string
            Output XML file name.

        keyval : dictionary
            Dictionary of keyword value pairs.

        Attributes
        ----------
        line : Line
            A Line class to hold the data.

    """
    def __init__(self, xmlFile=None, **keyval):
        BDP.__init__(self, xmlFile)
        # instantiate the line as a data member
        self.line = Line()
        self.setkey(keyval)
        self._version= "0.1.0"
