""" .. _BDPReader-api:

    BDPReader --- Converts BDP in XML format to in-memory BDP object.
    -----------------------------------------------------------------

    This module defines the BDPReader class.

"""

#system imports
from xml import sax
import os

# ADMIT imports
import admit.util.bdp_types as bt
import admit.util.utils as utils
from admit.xmlio.AdmitParser import AdmitParser
from admit.xmlio.ErrorHandler import ErrorHandler

class BDPReader(object):
    """ Class to read in a bdp file (xml style) and convert it to a BDP object in memory. Only the
        name of the bdp file (including any relative or absolute path) needs to be specified. The
        given file will be passed to the AdmitParser where it will be parsed. The resulting data
        will be inserted into a BDP object of the appropriate type (type is determined by the
        contents of the bdp file). The BDP object is the returned.

        Parameters
        ----------
        file : str
            File name (including any relative or absolute path) of the bdp file to be parsed and 
            converted to a BDP object.
            Default : None.

        Attributes
        ----------
            File name (including any relative or absolute path) of the bdp file to be parsed and 
            converted to a BDP object.

    """
    def __init__(self, file=None):
        self.file = file

    def read(self, file=None):
        """ Method to convert a bdp file to a BDP object. Only the file name (including relative
            or absolute path) needs to be given. The file is then parsed and the data inserted into
            the appropriate BDP object. The type of BDP is determined from the data in the bdp file
            itself. The resulting BDP object is returned.

            Parameters
            ----------
            file : str
                File name (including any relative or absolute path) of the bdp file to be parsed and 
                converted to a BDP object.
                Default : None

            Returns
            -------
            BDP object of appropriate type based on the given input file.
        """
        # error check the input
        if self.file is None:
            if file is not None:
                self.file = file
            else:
                raise Exception("File name must be specified.")
        # see if a path was also given with the file name, if not the used the current working
        # directory
        sloc = self.file.rfind("/")
        if sloc == -1:
            basedir = os.getcwd()
        else :
            basedir = self.file[:sloc]
        # instanstiate a parser
        BDPparser = sax.make_parser()
        BDPContentHandler = AdmitParser(basedir, self.file)
        # set the handlers
        BDPparser.setContentHandler(BDPContentHandler)
        BDPparser.setErrorHandler(ErrorHandler())
        # parse the file, craeting the appropriate BDP object
        BDPparser.parse(open(self.file))
        # return the BDP object
        return BDPContentHandler.getBDP()
