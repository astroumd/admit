"""
   .. _BDP-base-api:

   **BDP** --- Basic data product base.
   ------------------------------------

   This module defines the Basic Data Product (BDP) base class.
"""

import os
import xml.etree.cElementTree as et
import types
import admit.util.utils as utils
import admit.util.bdp_types as bt
from admit.util.Image import Image
from admit.util.MultiImage import MultiImage
from admit.util.Line import Line
from admit.util.Table import Table
from admit.xmlio.DtdReader import DtdReader
##import zipfile
#import admit.util.util as util
import admit.xmlio.XmlWriter as XmlWriter

_debug = False
#_debug = True

class BDP(object):
    """Basic Data Product base.

       Basic Data Products (BDPs) are data containers used to transport
       information within ADMIT, as well as deliver it to users in a
       persistent, well-defined format.

       Parameters
       ----------
       xmlFile : str, optional
           XML file associated with BDP (for persistence);
           defaults to ``None``.

       keyval : dict
           Dictionary of keyword value pairs.

       Attributes
       ----------
       gous : TBD
          TBD

       mous : TBD
          TBD

       sous : TBD
          TBD  (the official name is sous)

       project : TBD
          TBD

       xmlFile : str
          XML file associated with BDP (for persistence).

       _baseDir : str
           ADMIT project directory (None if unknown).

       _date : TBD
          Date of last edit.

       _taskid : int
           Originating ADMIT task ID number.

       _type : admit.util.bdp_types
          Concrete BDP type.

       _updated : bool
           Whether BDP has been modified since latest XML output.

    """
    _uid = 0
    """Class static BDP ID number."""

    def __init__(self, xmlFile=None, **keyval):
        # just some default values
        self.project = ""
        self.sous = ""
        self.mous = ""
        self.gous = ""
        self._date = ""                        # date of last edit
        self._type = self.__class__.__name__
        self.xmlFile = xmlFile                  # xml file associated with BDP
        self._baseDir = ""
        self._updated = False                   # has been updated
        self._taskid = -1
        self._version = "0.0.0"
        self._uid = BDP._uid
        BDP._uid = BDP._uid + 1
        if self.xmlFile is None:
            self.xmlFile = self._type + "_" + str(self._uid)
        self.setkey(keyval)

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + "\nBDP :" + bt.format.END + \
              bt.format.BOLD + self._type + bt.format.END
        for i, j in self.__dict__.iteritems():
            if isinstance(j, (Line, Image, MultiImage, Table)):
                print bt.format.BOLD + i + ": "
                print j
                continue
            print bt.format.BOLD + i + ": " + bt.format.END + str(j)
        return "\n"

    def getfiles(self):
        """ Return the filename(s) associated with the basic data in a BDP.

            Parameters
            ----------
            None

            Returns
            -------
            List of files

            Notes
            -----
            .. todo::
              Really should look for attribute .filename, but normally
              derived classes should implement these; see e.g. File_AT.
        """
        files = []
        for i in self.__dict__:
            if isinstance(getattr(self, i), Image):
                #print getattr(self, i).images
                for key in getattr(self, i).images:
                    files.append(getattr(self, i).images[key])
                #files.append(getattr(self, i).fileName)
        return files

    def show(self):
        """ Show the xmlFile name.

            Parameters
            ----------
            None

            Returns
            -------
            the xml file name

            Notes
            -----
            .. todo::
                Extend functionality to show more.
        """
        return self.xmlFile

    def baseDir(self, path=None):
        """ Get/set project base directory.

            Parameters
            ----------
            path : str, optional
                New project base directory (ignored if None).

            Returns
            -------
            Updated project base directory.

            Notes
            -----
            Unless empty, the base directory is guaranteed to end in os.sep.
        """
        if path is not None:
            if path and path[-1] != os.sep:
                path += os.sep
            self._baseDir = path
        return self._baseDir

    def update(self, new_state):
        """ Updates BDP state.

            Parameters
            ----------
            new_state : varies
                New BDP state.

            Returns
            -------
            None
        """
        if _debug:
            print "UPDATE: %s" % self.xmlFile
        self._updated = new_state

    def report(self):
        """ Report BDP properties in human readable format.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        print "===report==="
        print "BDP::%s" % self.xmlFile

    def setkey(self, name="", key={}):
        """ Sets keyword value(s).

            Two styles are possible:

            1. name = {key:val}            e.g. **setkey({"a":1})**

            2. name = "key", key = val     e.g. **setkey("a", 1)**

            Parameters
            ----------
            name : dict or str, optional
                Keyword/values pairs, or single keyword name; defaults to empty
                string.

            key : str, optional
                Keyword value; defaults to empty dictionary.

            init : bool, optional
                Whether keyword is being set for the first time.
        """
        if isinstance(name, dict):
            #1
            # check that the keys are valid first
            for i in name:
                if not self.haskey(i):
                    raise Exception("%s is not a valid key for %s." % (i, self._type))
                if type(getattr(self, i, None)) != type(name[i]):
                    if isinstance(name[i], Image) and isinstance(getattr(self, i, None), MultiImage):
                        continue
                    raise Exception("You cannot change the data type of an BDP keyword. Type for %s is %s but needs to be %s" % (i, str(type(name[i])), str(type(getattr(self, i, None)))))
            for i in name:
                if isinstance(name[i], Image) and isinstance(getattr(self, i, None), MultiImage):
                    t = getattr(self, i, None)
                    t.addimage(name[i])
                    self.setkey(i, t)
                    return
                setattr(self, i, name[i])
        elif not name == "":
            #2
            # check that the key is valid
            if not self.haskey(name):
                raise Exception("%s is not a valid key for %s." % (name, self._type))
            if type(getattr(self, name, None)) != type(key):
                if isinstance(key, Image) and isinstance(getattr(self, name, None), MultiImage):
                    t = getattr(self, name, None)
                    t.addimage(key)
                    self.setkey(name, t)
                    return
                else:
                    raise Exception("You cannot change the data type of an BDP keyword. Type for %s is %s but needs to be %s" % (name, str(type(key)), str(type(getattr(self, name, None)))))

            setattr(self, name, key)
        else:
            # @todo need to give more feedback to user
            raise Exception("Invalid keys given to setkey")

    def haskey(self, key):
        """
        Query if a key exists for an BDP.

        Parameters
        ----------
        key : str
            Keyword name.

        Returns
        -------
            True if keyword is present, else False.
        """
        if getattr(self, key, None) is None:
            return False
        return True

    def get(self, key):
        """
        Access an attribute.

        Parameters
        ----------
        key : str
            Keyword name.

        Returns
        -------
        varies
            Attribute value if keyword is present, else ``None``.

        """
        if _debug:
            print "BDP::get %s" % (key)
        return getattr(self, key, None)

    def write(self, xmlFile=None):
        """ Writes the BDP to an XML file.

            Parameters
            ----------
            xmlFile : str, optional
                Output XML file name; defaults to eponymous internal attribute.

            Notes
            -----
            Do not edit unless you know what you are doing as all BDP's rely on
            this method to work properly.
            Normally the xmlFile here should be the full path.
        """
        dtdRead = DtdReader(self._type + ".dtd")
        order = dtdRead.getOrder()
        dtd = dtdRead.getDtd()
        typs = dtdRead.getTypes()

        if xmlFile is None:
            raise Exception("No output files was specified")
     
        root = et.Element("BDP")
        root.set("type", self._type)

        XmlWriter.XmlWriter(self, order, typs, root)

        #Return a pretty-printed XML string for the Element.
        rough_string = et.tostring(root, 'utf-8')

        temp = rough_string.replace(">", ">\n")
        temp = temp.replace("</", "\n</")

        outFile = open(xmlFile + ".bdp", 'w')
        outFile.write("<?xml version=\"1.0\" ?>\n")
        # write out the dtd info at the top
        outFile.write("<!DOCTYPE BDP [\n\n")
        for line in dtd:
            outFile.write(line)
        outFile.write("]>\n\n")
        outFile.write(temp)
        outFile.close()

        #zFile = zipfile.ZipFile(self.xmlFile + ".zip", 'w', compression=zipfile.ZIP_DEFLATED)
        #zFile.write(self.xmlFile)
        #zFile.close()

    def delete(self, delfiles=True):
        """ Method to delete the BDP. This method will search through all class
            variables and delete any images since they contain external files, and
            then deletes the BDP's XML file.

            Parameters
            ----------
            basedir : str, optional
                XML file directory; defaults to current directory.

            delfiles : bool, optional
                Whether or not to delete the actual files on disk; defaults to True.

            Notes
            -----
            It is recommended that any BDP that stores images inside of lists, 
            dictionaries, tuples, etc. override this method with a customized
            version.
        """
        for i in self.__dict__:
            if isinstance(getattr(self, i), MultiImage):
                getattr(self, i).delete(self._baseDir, delfiles)
                del i
        if delfiles:
            utils.remove(self._baseDir + os.sep + self.xmlFile + ".bdp")

    def getdir(self):
        """ Method to get the subdirectory(s) of the current BDP relative to the
            ADMIT working directory.

            Parameters
            ----------
            None

            Returns
            -------
            String containing the current BDPs subdirectory
        """
        # @todo   fails if the BDP is in the main admit directory and returns [:-1]
        loc = self.xmlFile.rfind("/")
        return self.xmlFile[:loc]

    def isequal(self, bdp):
        """ Tests for equality with another BDP.

            Parameters
            ----------
            bdp : BDP
                The other BDP.

            Returns
            -------
                True if the BDP types and contents match, else False.
        """
        try:
            if bdp.get("_type") != self._type:
                print "BDP types are not the same: " + bdp.get("_type") + " vs " +self._type
                return False
            for i in self.__dict__:
                if isinstance(i, (types.TypeType, types.ClassType)):
                    if not(isinstance(i, Image) or isinstance(i, Line) or isinstance(i.Table)):
                        continue
                    if not getattr(self, i).isequal(getattr(bdp, i)):
                        print "Attribute %s does not match" % (i)
                        return False

                elif cmp(getattr(self, i), getattr(bdp, i)) != 0:
                    print "Attribute %s does not match" % (i)
                    return False
        except:
            return False
        return True
