""" **LineSegment_BDP** --- LineSegment_AT data (line segment information).
    -----------------------------------------------------------------------

    This module defines the LineSegment_BDP class.
"""

# ADMIT imports
#from Table_BDP import Table_BDP
#from Image_BDP import Image_BDP
from LineList_BDP import LineList_BDP
import admit.util.utils as utils

# system imports
import numpy as np

class LineSegment_BDP(LineList_BDP):
    """ LineSegment BDP class.

        This class contains a list of spectral line segments identified by the LineSegment
        AT. The columns in the table are: frequency (rest frequency in
        GHz), uid (unique identifier consisting of "U" and rest
        frequency), startchan (starting channel in the spectral window), endchan 
        (ending channel in the spectral window).

        Parameters
        ----------
        xmlFile : str
            Output XML file name.

        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        table : Table
            Instance of he Table class to hold the spectral line information.

        veltype : str
            Velocity definition used for the spectrum.
            Default: "vlsr".

        ra : str
            The RA of where the spectrum was taken.
            Default: "".

        dec : str
            The declination of where the spectrum was taken.
            Default: "".

        nsegs : int
            The number of segments in the table.
            Default: 0.

    """

    def __init__(self, xmlFile=None, **keyval):
        LineList_BDP.__init__(self, xmlFile)
        self.veltype = "vlsr"
        self.ra = ""
        self.dec = ""
        self.nsegs = 0
        self.table.setkey("columns", utils.linelist_columns)
        self.table.setkey("units", utils.linelist_units)
        self.table.description="Line Segments"
        self.table.data = np.array([], dtype=object)
        self.setkey(keyval)
        self._version= "0.1.0"

    def addRow(self, row):
        """ Method to add a row to the table

            Parameters
            ----------
            row : LineData object
                LineData object containing the data

            Returns
            -------
            None

        """
        data = []
        # build the row from the data
        for col in utils.linelist_columns:
            data.append(row.getkey(col))
        self.table.addRow(data)
        self.nsegs += 1

    def __len__(self):
        return self.nsegs
