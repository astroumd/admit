""" .. _SourceList-bdp-api:

    **SourceList_BDP** --- SFind2D_AT data (image and table).
    ---------------------------------------------------------

    This module defines the SourceList_BDP class.
"""

# ADMIT imports
from Table_BDP import Table_BDP
from Image_BDP import Image_BDP

# system imports
import numpy as np


class SourceList_BDP(Table_BDP, Image_BDP):
    """ SourceList BDP class.

        This class contains a list of sources.

        Parameters
        ----------
        xmlFile : str
            Output XML file name.

        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        table : Table
            Instance of the Table class to hold the source information.

    """
    def __init__(self, xmlFile=None, **keyval):
        Table_BDP.__init__(self, xmlFile)
        Image_BDP.__init__(self, xmlFile)
        self.nsources = 0
        self.table.setkey("columns", ["Name", "RA", "DEC", "Flux", "Peak",    "Major",  "Minor",  "PA"])
        self.table.setkey("units",   ["",     "",   "",    "Jy",   "Jy/beam", "arcsec", "arcsec", "deg"])
        self.table.data = np.array([], dtype=object)
        self.setkey(keyval)
        self._version= "0.1.0"

    def addRow(self, row):
        """ Method to add a row to the table

            Parameters
            ----------
            row : array like
                the row to add

            Returns
            -------
            None

        """
        self.nsources += 1
        self.table.addRow(row)

    def __len__(self):
        return len(self.table)
