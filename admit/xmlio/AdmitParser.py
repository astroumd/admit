"""
    AdmitParser --- Specialized parser for ADMIT XML files.
    -------------------------------------------------------

    This module defines the AdmitParser class.
"""
from xml import sax
import copy
import numpy as np

from admit.util.AdmitLogging import AdmitLogging as logging
from admit.xmlio.DTDParser import DTDParser
import admit.util.bdp_types as bt
import admit.util.utils as utils
import admit.Summary as Summary
from admit.AT import AT
import admit.FlowManager as fm
import admit.util.admit_ast as aast

class AdmitParser(sax.handler.ContentHandler):
    """ Specialized XML parser for admit and bdp parsing.

        Parameters
        ----------
        basedir : str
            The base directory being used to read in the ADMIT files.

        xmlFile : str
            The file to parse.
            Deafult: "admit.xml".

        Attributes
        ----------
        xmlFile : str
            The file to parse.

        basedir : str
            The base directory being used to read in the ADMIT files.

        dtd : DtdReader
            Instance of the DtdReader to use.

        AT : List
            List for keeping track of the AT's found.

        curAT : AT
            Instance of the current AT being reconstructed.

        type : str
            Type of the curAT.

        name : str
            Name of the current node being parsed.

        ndarr : List
            List of elements that are numpy arrays.

        sets : List
            List of elements that are sets.

        userData : Dict
            Dictionary for the user data.

        summaryData : Dict
            Dictionary for the summaryData.

        summaryEntry : SummaryEntry
            Current instance of the SummaryEntry being reconstructed.

        flowmanager : FlowManager
            Local copy of the FlowManager for reconstruction.

        projmanager : Dict
            Project ID to base directory map.

        Util : various classes
            The current utility class being reconstructed.

        MultiImage : MultiImage class instance
            The current MultiImage being reconstructed.

        inflow : Boolean
            Whether the parser is currently reconstructing the flow manager.

        inAdmit : Boolean
            Whether the parser is currently reconstructing the ADMIT base
            class.

        inUtil : Boolean
            Whether the parser is currently reconstructing a utility class.

        inMulti : Boolean
            Whether the parser is currently reconstructung a MultiImage.

        inKeys : Boolean
            Whether the parser is currently reconstructing the keys of an AT.

        inSummary : Boolean
            Whether the parser is currently reconstructing the summary data.

        inSummaryEntry : Boolean
            Whether the parser is currently reconstructing a SummaryEntry.

        utilType : str
            The type of the current utility class being reconstructed.

        utilName : str
            The name of the current utility class being reconstructed.

        multiName : str
            The name of the MultiImage currently being reconstructed.

        summaryName : str
            The name of the summary being reconstructed.

        summaryEntryName : str
            The name of the SummaryEntry being reconstructed.

        admit : ADMIT
            The base class being reconstructed.

        metadataName : str
            The name of the current metadata node.

        inBDP : Boolean
            Whether the parser is currently reconstructing a BDP.

        inAT : Boolean
            Whether the parser is currently reconstructing an AT.

        tempdata : str
            String for holding large data that need to be reconstructed.
    """
    def __init__(self, basedir="", xmlFile="admit.xml"):
        self.xmlFile = xmlFile
        self.basedir = basedir
        # initialize the parent class
        sax.handler.ContentHandler.__init__(self)
        # get the dtd info
        self.dtd = DTDParser(xmlFile)
        self.dtd.parse()
        self.AT = []
        # intialize all of the variables that track everything as it is
        # being reconstructed
        self.curAT = None
        self.BDP = None
        self.type = None
        self.name = None
        self.ndarr = []
        self.sets = []
        self.userData = None
        self.summaryData = None
        self.summaryEntry = None
        self.flowmanager = None
        self.projmanager = None
        self.inflow = False
        self.inAdmit = False
        self.inKeys = False
        self.inSummary = False
        self.inSummaryEntry = False
        self.summaryName = None
        self.summaryEntryName = None
        self.metadataName = None
        self.admit = None
        self.Util = None
        self.MultiImage = None
        self.inUtil = False
        self.inMulti = False
        self.utilType = ""
        self.utilName = ""
        self.multiName = ""
        self.inBDP = False
        self.inAT = False
        self.tempdata = ""
        self.flowdata = ""

    def getBDP(self):
        """ Return the current BDP

            Parameters
            ----------
            None

            Returns
            -------
            The current BDP
        """
        # return the generated BDP
        return copy.deepcopy(self.BDP)

    def setadmit(self, admit):
        """ Set the base class to the given class

            Parameters
            ----------
            admit : ADMIT
                The class to set the base to

            Returns
            -------
            None
        """
        self.admit = admit

    def getflowmanager(self):
        """ Returns the FlowManager instance

            Parameters
            ----------
            None

            Returns
            -------
            The current FlowManager instance
        """
        return self.flowmanager

    def getAT(self):
        """ Return the list of reconstructed AT's

            Parameters
            ----------
            None

            Returns
            -------
            List of AT's
        """
        # return the generated AT list
        return self.AT

    def startElement(self, name, attrib):
        """ Method called whenever a new element is found. Dtd validation is
            done for each node and attribute. This method is only called by the
            SAX parser iteself.

            Parameters
            ----------
            name : str
                The name of the current node

            attrib : Dict
                Dictionary of any attributes and their values that was found by
                the parser

            Returns
            -------
            None
        """
        # get the type of the data
        self.tempdata = ""
        temp = str(attrib.get("type"))
        # figure out where the node belongs
        if bt.ADMIT == name or temp == bt.AT:
            self.dtd.check(name.upper())
        else:
            if self.inAT:
                self.dtd.check(name + "_" + self.curAT.show().upper(), "type",
                               temp)
            else:
                self.dtd.check(name, "type", temp)
        if name == bt.FLOWMANAGER:
            self.inflow = True
        self.name = name
        if self.inBDP:
            self.dtd.check(name, "type", temp)
        if name == "_keys":
            self.inKeys = True
            return
        # find out what type of data the node contains
        if temp == bt.STRING:
            self.type = str()
        elif temp == bt.BOOL:
            self.type = bool()
        elif temp == bt.FLOAT:
            self.type = float()
        elif temp == bt.LONG:
            self.type = long()
        elif temp == bt.NONE:
            target = None
            # handle the utility, BDP and AT classes
            if self.inUtil:
                target = self.Util
            elif self.inBDP:
                target = self.BDP
            elif self.inAT:
                target = self.curAT
            else:
                target = self.admit
            try:
                setattr(target, self.name, None)
            except AttributeError:
                print "Data member %s is not a member of %s. This may be due to a version mismatch between the data and your software, attempting to continue." % \
                      (self.name, str(type(target)))
            except:
                raise
        elif temp == bt.DICT:
            self.type = dict()
            self.ndarr = aast.literal_eval(attrib.get("ndarray"))
            self.sets = aast.literal_eval(attrib.get("set"))
            tname = name
            if self.inAT:
                tname += "_" + self.curAT.show().upper()
            self.dtd.check(tname, "ndarray", bt.STRING)
            self.dtd.check(tname, "set", bt.STRING)
        elif temp == bt.LIST:
            self.type = list()
            self.ndarr = aast.literal_eval(attrib.get("ndarray"))
            self.sets = aast.literal_eval(attrib.get("set"))
            tname = name
            if self.inAT:
                tname += "_" + self.curAT.show().upper()
            self.dtd.check(tname, "ndarray", bt.STRING)
            self.dtd.check(tname, "set", bt.STRING)
        elif temp == bt.SET:
            self.type = set()
            self.ndarr = aast.literal_eval(attrib.get("ndarray"))
            self.sets = aast.literal_eval(attrib.get("set"))
            tname = name
            if self.inAT:
                tname += "_" + self.curAT.show().upper()
            self.dtd.check(tname, "ndarray", bt.STRING)
            self.dtd.check(tname, "set", bt.STRING)
        elif temp == bt.INT:
            self.type = int()
        elif temp == bt.TUPLE:
            self.type = tuple()
            self.ndarr = aast.literal_eval(attrib.get("ndarray"))
            self.sets = aast.literal_eval(attrib.get("set"))
            tname = name
            if self.inAT:
                tname += "_" + self.curAT.show().upper()
            self.dtd.check(tname, "ndarray", bt.STRING)
            self.dtd.check(tname, "set", bt.STRING)
        elif temp == bt.NDARRAY:
            self.type = np.ndarray([])
        elif name == bt.ADMIT:
            self.inAdmit = True
        elif temp.title() in bt.UTIL_LIST or temp.upper() == bt.MULTIIMAGE:
            self.inUtil = True
            if temp.upper() == bt.MULTIIMAGE:
                self.multiName = name
                self.MultiImage = utils.getClass("util", "MultiImage")
                self.inMulti = True
            else:
                self.Util = utils.getClass("util", temp.title())
                self.utilName = name
                self.utilType = temp
        elif temp == bt.AT:
            if self.flowmanager is None:
                raise Exception("FlowManager not initialized, xml in wrong order")
            self.inAT = True
            try:
                self.curAT = utils.getClass("at", name)
            except Exception, e:
                raise Exception("Could not create class of type %s because %s" % (name, str(e)))
        elif name == bt.BDP:
            self.type = temp
            self.inBDP = True
            try:
                self.BDP = utils.getClass("bdp", temp)
            except Exception, e:
                raise Exception("Could not create class of type %s because %s" % (temp, str(e)))
        elif temp == bt.SUMMARY:
            self.summaryData = Summary.Summary()
            self.inSummary = True
            self.summaryName = name
        elif temp == bt.SUMMARYENTRY:
            self.summaryEntry = Summary.SummaryEntry()
            self.inSummaryEntry = True
            self.summaryEntryName = name
        elif name == "metadata" and self.inSummary:
            self.metadataName = str(attrib.get("name"))
            self.dtd.check(name, "name", bt.STRING)
            self.summaryData._metadata[self.metadataName] = []

    def endElement(self, name):
        """ Method called whenever the end of an xml element is reached. This
            method is only called by the SAX parser iteself.

            Parameters
            ----------
            name : str
                The name of the node that just ended

            Returns
            -------
            None
        """
        # reset the tracking stuff, add BDP's to AT's, AT's to the flowmanager
        # reconstruct any nodes that spanned multiple lines
        if name == self.utilName:
            # add the utility classes to the appropriate parent class
            # Images always get added to MultiImages
            if self.inMulti:
                self.MultiImage.addimage(copy.deepcopy(self.Util), self.Util.name)
            elif self.inBDP:
                setattr(self.BDP, self.utilName, copy.deepcopy(self.Util))
            elif self.inAT:
                setattr(self.curAT, self.utilName, copy.deepcopy(self.Util))
            self.inUtil = False
            self.utilName = ""
        elif name == self.multiName:
            if self.inBDP:
                setattr(self.BDP, self.multiName, copy.deepcopy(self.MultiImage))
            elif self.inAT:
                setattr(self.curAT, self.multiName, copy.deepcopy(self.MultiImage))
            self.multiImageName = ""
            self.inMulti = False
            self.inUtil = False
        elif name == bt.BDP:
            # one last validation run
            self.BDP._baseDir = self.basedir
            if not self.dtd.checkAll():
                logging.info("Some required nodes missing from xml file, attempting to continue anyway.")
        elif name == bt.FLOWMANAGER:
            temp = aast.literal_eval(self.flowdata)
            for key in ["depsmap", "varimap"]:
                if key in temp:
                    temp[key] = eval(temp[key])
            self.flowmanager = fm.FlowManager(**temp)

            self.inflow = False
        elif isinstance(self.type, str):
            if self.inUtil:
                target = self.Util
            elif self.inBDP:
                target = self.BDP
            elif self.inAT:
                target = self.curAT
            elif self.inSummaryEntry:
                target = self.summaryEntry
            elif name == "projmanager":
                target = self
            else:
                target = self.admit

            self.setattr(target, name, self.tempdata)
            self.tempdata = ""
        elif isinstance(self.type, list) or isinstance(self.type, dict) \
           or isinstance(self.type, tuple) or isinstance(self.type, set):
            temp = aast.literal_eval(self.tempdata)
            if self.inUtil:
                target = self.Util
            elif self.inBDP:
                target = self.BDP
            elif self.inAT:
                target = self.curAT
            elif self.inSummaryEntry:
                target = self.summaryEntry
            elif name == "projmanager":
                target = self
            else:
                target = self.admit
            for i in self.ndarr:
                temp[i] = np.array(temp[i], dtype=object)
            for i in self.sets:
                temp[i] = set(temp[i])
            if isinstance(self.type, tuple):
                temp = tuple(temp)
            elif isinstance(self.type, set):
                temp = set(temp)
            try:
                self.setattr(target, name, temp)
            except AttributeError:
                logging.info("Data member %s is not a member of %s. This may be due to a version mismatch between the data and your software, attempting to continue." % (self.name, str(type(target))))
            except:
                raise
        elif isinstance(self.type, np.ndarray):
            temp = aast.literal_eval(self.tempdata)
            if self.inUtil:
                target = self.Util
            elif self.inBDP:
                target = self.BDP
            elif self.inAT:
                target = self.curAT
            else:
                target = self.admit
            try:
                self.setattr(target, self.name, np.array(temp, dtype=object))
            except AttributeError:
                logging.info("Data member %s is not a member of %s. This may be due to a version mismatch between the data and your software, attempting to continue." % (self.name, str(type(target))))
            except:
                raise
        elif self.inAT and name == self.curAT.show():
            self.inAdmit = False
            # one last validation run
            self.curAT._bdp_in = [None] * len(self.curAT._bdp_in_map)
            self.curAT._bdp_out = [None] * len(self.curAT._bdp_out_map)
            self.curAT._baseDir = self.basedir
            at = copy.deepcopy(self.curAT)
            self.AT.append(at)
            self.flowmanager[at._taskid] = at
            self.curAT = None
            self.inAT = False
        elif name == bt.ADMIT:
            self.inAdmit = False
            if not self.dtd.checkAll():
                print "Some required nodes missing from admit.xml file, attempting to continue anyway"
        elif name == "_keys":
            self.inKeys = False
        elif name == self.summaryEntryName:
            self.summaryData._metadata[self.metadataName].append(copy.deepcopy(self.summaryEntry))
            self.summaryEntryName = None
            self.inSummaryEntry = False
        elif name == self.summaryName:
            self.inSummary = False
        elif name == self.metadataName:
            self.metadataName = None
        else:
            self.ndarr = []
            self.sets = []
        self.type = None
        self.name = None
        self.ndarr = False

    def setattr(self, target, name, value):
        """ Method to set attributes in a class

            Parameters
            ----------
            target : object
                The class to which the paremeters is being set

            name : str
                The name of the attribute to set

            value : various
                The value to set the attribute to
        """
        # if we are in the keys the treat the special
        if self.inKeys:
            target.setkey(name, value, True)
        else:
            setattr(target, name, value)

    def getattr(self, target, name):
        """ Method to get the value of a specific data member from the given class

            Parameters
            ----------
            target : object
                The class from which the data value will be obtained

            name : str
                The name of the data member whose value will be obtained

            Returns
            -------
            Various, the value of the requested data member, None if it does not exist

        """
        if self.inKeys:
            target.getkey(name)
        else:
            if hasattr(target, name):
                return target.get(name)
            else:
                return None

    def characters(self, ch):
        """ Method called whenever characters are detected in an xml node
            This method does some dtd validation. This
            method is only called by the SAX parser iteself.

            Parameters
            ----------
            ch : unicode characters

            Returns
            -------
            None
        """
        target = None
        char = str(ch).strip()
        if char.isspace() or not char:
            return
        # determine which class the data are getting writtrn to
        if self.inUtil:
            target = self.Util
        elif self.inBDP:
            target = self.BDP
        elif self.inAT:
            target = self.curAT
        elif self.inSummaryEntry:
            target = self.summaryEntry
        elif self.inSummary:
            target = self.summaryData
        else:
            target = self.admit
        # a list or dictionary has to be decoded
        if isinstance(self.type, list) or isinstance(self.type, dict) \
           or isinstance(self.type, tuple) or isinstance(self.type, set) \
           or isinstance(self.type, np.ndarray) or isinstance(self.type, str):
            if self.inflow:
                self.flowdata += char
            else:
                self.tempdata += char
        else:
            # check the version
            if self.name == "_version":
                ver = self.getattr(target, self.name)
                vercheck = utils.compareversions(ver, str(char))
                if vercheck < 0: # newer read in
                    logging.warning("Version mismatch for %s, data are a newer version than current software, attempting to continue." % target.getkey("_type"))
                elif vercheck > 0: # older read in
                    logging.warning("Version mismatch for %s, data are an older version than current software, attempting to continue." % target.getkey("_type"))
            else:
                try:
                    self.setattr(target, self.name, self.getData(char))
                except AttributeError:
                    logging.info("Data member %s is not a member of %s. This may be due to a version mismatch between the data and your software, attempting to continue." % (self.name, str(type(target))))
                except:
                    raise
        del ch

    def close(self):
        """ Method to close out the reader, called only by the sax parser

            Parameters
            ----------
            None

            Returns
            -------
            None

        """
        return

    def getData(self, item):
        """ Method used to convert string to designated type.

            Parameters
            ----------
            input: str
                The string to convert

            Returns
            -------
            Various types, based on the expected type of the xml node
        """
        if isinstance(self.type, bool):
            return bool(int(item))
        if isinstance(self.type, int):
            return int(item)
        if isinstance(self.type, long):
            return long(item)
        if isinstance(self.type, float):
            return float(item)
        if isinstance(self.type, str):
            return str(item)
