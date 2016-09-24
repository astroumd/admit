""" .. _Source-api:

    **Source** --- Astronomical source metadata.
    --------------------------------------------

    This module defines the Source class for SOURCE entries in BDPs.
"""
# system imports
import xml.etree.cElementTree as et

# ADMIT imports
import bdp_types as bt
from UtilBase import UtilBase


class Source(UtilBase):
    """ Class for holding information on a specific source.

        Parameters
        ----------
        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        name : str
            Name/Label of the source.
            Default: "".

        ra : string
            Right Ascension, in CASA hms notation.

        dec : string
            Declination, in CASA hms notation.

        flux : float
            Total flux of source, in Jy.

        peak : float
            Peak value at the center, in Jy/beam.

        major : float
            Major axis of the fitted gaussian. This will include the beam.

        minor : float
            Minor axis of the fitted gaussian. This will include the beam.

        pa : float
            Position angle of the beam, east from north, in degrees.

    """
    def __init__(self, **keyval):
        self.name = ""
        self.ra = ""
        self.dec = ""
        self.flux = 0.0
        self.peak = 0.0
        self.major = 0.0
        self.minor = 0.0
        self.pa = 0.0
        UtilBase.__init__(self, **keyval)

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + "Source :" + bt.format.END
        for i, j in self.__dict__.iteritems():
            print bt.format.BOLD + i + ": " + bt.format.END + str(j)
        return ""

    def isequal(self, source):
        """ Experimental method to compare 2 sources

            Parameters
            ----------
            source : Source
                The source to compare this one to.

            Returns
            -------
            Boolean whether or not the two classes contain the same data.

        """
        try:
            for i in self.__dict__:
                if cmp(getattr(self, i), getattr(source, i)) != 0:
                    return False
        except:
            return False
        return True
