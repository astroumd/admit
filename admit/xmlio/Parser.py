""" .. _Parser-api:

    Parser --- Converts an ADMIT project on disk to in-memory objects.
    ------------------------------------------------------------------

    This module is for parsing the input xml files, both admit.xml and the
    general bdp xml files.

"""

# system imports
from xml import sax
import copy
import os

# ADMIT imports
from admit.xmlio.AdmitParser import AdmitParser
from admit.xmlio.ErrorHandler import ErrorHandler
from admit.xmlio.BDPReader import BDPReader
from admit.AT import AT
from admit.util.AdmitLogging import AdmitLogging as logging
from admit.util import utils


class Parser(object):
    """ Main XML parsing class.

        This class parses the main xml file (usually admit.xml) and reads in all
        AT and ADMIT data. It then searches for all BDP's in the working
        directory and subdirectories. These BDP files are then parsed and added
        to their parent ATs.

        Parameters
        ----------
        base : ADMIT
          Instance of the base ADMIT class to add everything to.
          No Default.

        baseDir : str
          The root directory of the admit tree.
          Default: "" (current dirctory).

        xmlFile : str
          The root admit xml file to parse.
          Default: "".

        Attributes
        ----------
        xmlFile : str
          String for the xml file to parse.

        parser : SAX parser
          The parser to use.

        admit : ADMIT
          The instance of the ADMIT class to add everything to.

        baseDir : str
          The root directory for working.

        tasks : List
          A list of all AT's found.

        userData : dict
          Dictionary for user data.

        summaryData : dict
          Summary data.

        flowmanager : FlowManager
          Temporary FM for reading in the data.

        projmanager: dict
          Project ID to base directory map.

    """
    def __init__(self, base, baseDir="", xmlFile=""):
        self.xmlFile = xmlFile
        self.parser = sax.make_parser()  # initialize the parser
        self.admit = base
        self.baseDir = baseDir
        self.tasks = None
        self.userData = None
        self.summaryData = None
        self.flowmanager = None
        self.projmanager = None

    def getTasks(self):
        """ Return the list of AT's that have been read in

            Parameters
            ----------
            None

            Returns
            -------
            List
                List of the AT's from the xml file

        """
        return self.tasks

    def getflowmanager(self):
        """ Return the local copy of the FlowManager

            Parameters
            ----------
            None

            Returns
            -------
            FlowManager
                Copy of the local FlowManager that was read in from XML.
        """
        return self.flowmanager

    def getSummary(self):
        """ Return the local copy of the summaryData

            Parameters
            ----------
            None

            Returns
            -------
            summaryData
                Copy of the local summaryData that was read in from XML.
        """
        return self.summaryData

    def addBDPtoAT(self, bdp):
        """ Method to add a BDP to an AT. The AT is not specified, but the
            _taskid attribute of the BDP is used to identify the necessary AT.

            Parameters
            ----------
            bdp : BDP
                Any valid BDP, to be added to an existing AT.

            Returns
            -------
            None

        """
        found = False
        cp = copy.deepcopy(bdp)
        # find the AT we need
        for at in self.tasks:
            # see if the ID's match
            if at._taskid == bdp._taskid:
                found = True
                # set the base directory of the BDP
                cp.baseDir(at.baseDir())
                # add it to the correct slot
                at._bdp_out[at._bdp_out_map.index(cp._uid)] = cp
                break
        if not found:
            logging.info("##### Found orphaned BDP with type %s in file %s" % \
                (bdp._type, bdp.xmlFile))

    def parse(self, doParse=True):
        """ Method that controls the parsing flow. First reads in the root xml
            file and then any BDP files that were found.

            Parameters
            ----------
            doParse : Boolean
                Whether or not to actually parse the XML
                Default: True

            Returns
            -------
            None
        """
        if self.xmlFile is not None:
            # set up the parser, error handler,a nd content handler
            contentHandler = AdmitParser(self.baseDir, self.baseDir + self.xmlFile)
            contentHandler.setadmit(self.admit)
            errorHandler = ErrorHandler()
            self.parser.setContentHandler(contentHandler)
            self.parser.setErrorHandler(errorHandler)
            if doParse:
                # parse admit.xml
                self.parser.parse(open(self.baseDir + self.xmlFile))
                # get all of the bits and assemble the admit class content
                self.tasks = contentHandler.getAT()
                self.flowmanager = contentHandler.getflowmanager()
                self.projmanager = contentHandler.projmanager
                self.summaryData = contentHandler.summaryData
                files = utils.getFiles(self.baseDir)
                for fl in files:
                    # search for all BDP's and load them
                    BDPreader = BDPReader(fl)
                    # return the generated BDP class
                    self.addBDPtoAT(BDPreader.read())
                for at in self.tasks:
                    if not at.getProject():
                        at.baseDir(self.baseDir)
                    at.checkfiles()
