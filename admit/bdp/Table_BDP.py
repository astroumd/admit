""".. _Table-bdp-api:

   **Table_BDP** --- Tabular data base.
   ------------------------------------

   This module defines the Table_BDP class.
"""

# get the main BDP base class
from BDP import BDP

# get the table base class
from admit.util.Table import Table


# set up the inheritance
class Table_BDP(BDP):
    """ Table Basic Data Product.

        Table base class for use in BDP's. BDP's that contain tables
        should inherit from this class. In the instance where more than
        one table is needed then the class should instantiate instances
        of the Table class directly.

        Parameters
        ----------
        xmlFile : string
            Output XML file name.

        keyval : dictionary
            Dictionary of keyword value pairs.

        Attributes
        ----------
        table : Table
            A Table class to hold the data.
    """
    def __init__(self, xmlFile=None, **keyval):
        BDP.__init__(self, xmlFile)
        # instantiate a table as a data member
        self.table = Table()
        self.setkey(keyval)
        self._version= "0.1.0"
