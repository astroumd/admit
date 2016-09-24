""" .. _DtdReader-api:

    DtdReader --- Reads a DTD file.
    -------------------------------

    This module defines the DtdReader class.

"""
import os


class DtdReader(object):
    """ Class for reading in a dtd file and accumulating all of the different 
        bits.

        Parameters
        ----------
        fileName : str
            The name of the dtd file to read (e.g. Moment_BDP.dtd).

        Attributes
        ----------
        fileName : str
            The name of the dtd file to read (e.g. Moment_BDP.dtd).

        order : List
            Listing of the order that nodes in the xml should appear.

        types : Dict
            Dictionary for the type of data for each node (e.g. bt.INT).

        dtd : List
            Listing of the dtd contents to be written at the top of an xml
            file.

        keys : List
            List of the keys found for the top level nodes.
    """
    def __init__(self, fileName):
        self.fileName = os.path.dirname(os.path.realpath(__file__)) + os.sep + "dtd" + os.sep + fileName
        self.order = []
        self.types = {}
        self.dtd = []
        self.keys = []
        self.parse()

    def parse(self):
        """ Method to parse the given dtd file

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        #print self.fileName
        # open the dtd file and read the contents
        f = open(self.fileName, 'r')
        lines = f.readlines()
        mainLine = ""

        # parse each line and get the relevant information
        for line in lines:
            #print "LINE ",line
            #print "ELEMENT ADMIT" in line
            if "ELEMENT BDP" in line or "ELEMENT ADMIT" in line or "_AT\t" in line or "_AT2\t" in line:
                mainLine = line
            if "!ELEM" in line or "!ATT" in line:
                temp = line.split()
                if " type " in line:
                    temp = line.split()
                    self.types[temp[1]] = temp[3].replace("(", "").replace(")", "")
                if "ELEMENT _keys" in line:
                    keys = line.split()[2]
                    keys = keys.replace("?", "")
                    keys = keys.replace("*", "")
                    keys = keys.replace("(", "")
                    keys = keys.replace(")", "")
                    keys = keys.replace(">", "")
                    self.keys = keys.split(",")
                self.dtd.append(line)
        #print "ML",mainLine
        listing = mainLine.split()[2]
        listing = listing.replace("?", "")
        listing = listing.replace("*", "")
        listing = listing.replace("(", "")
        listing = listing.replace(")", "")
        listing = listing.replace(">", "")
        self.order = listing.split(",")
        f.close()

    def getOrder(self):
        """ Returns the order attribute

            Parameters
            ----------
            None

            Returns
            -------
            List containing the order nodes should appear
        """
        return self.order

    def getDtd(self):
        """ Returns the contents of the dtd attribute

            Parameters
            ----------
            None

            Returns
            -------
            List of the lines of the dtd
        """
        return self.dtd

    def getKeys(self):
        """ Returns the contents of the keys attribute

            Parameters
            ----------
            None

            Returns
            -------
            List containing the keys in the main node
        """
        return self.keys

    def getTypes(self):
        """ Returns the contents of the types attribute

            Parameters
            ----------
            None

            Returns
            -------
            Dictionary with the node names and data types
        """
        return self.types
