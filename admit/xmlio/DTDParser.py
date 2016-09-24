""" .. _DTDParser:

    DTDParser --- Parses DTD information within an XML file.
    --------------------------------------------------------

    This module defines the DTDParser class.
"""

from admit.util.AdmitLogging import AdmitLogging as logging
import pprint
pp = pprint.PrettyPrinter(indent=4)

class DTDParser(object):
    """ Class for parsing a dtd and holding the data for validation with XML.
        Reads in the dtd information at the top of the given file and
        constructs a dictionary based on its contents. Validation is done
        against this dictionary. A customized DTD validator was needed as there
        is no dtd validator for the SAX parser in python at the time this code
        was written.

        Parameters
        ----------
        xmlFile : str
            The xml file to read the dtd from.
            Default: None.

        Attributes
        ----------
        xmlFile : str
            The xml file to read the dtd from.

        entities : dict
            Dictionary for the memory model of the dtd.

        at : AT
            The current AT.
    """
    def __init__(self, xmlFile=None):
        self.xmlFile = xmlFile
        self.entities = dict()
        self.at = None

    def checkAll(self):
        """ Method to check the dtd structure to see if all expected
            nodes were found.

            Parameters
            ----------
            None

            Returns
            -------
            Boolean, whether or not all nodes were found

        """
        #pp.pprint(self.entities)
        for i in self.entities:
            if not self.entities[i]["found"]:
                print self.xmlFile
                logging.info(str(i) + " not found")
                return False
            for a in self.entities[i]["attrib"]:
                if not self.entities[i]["attrib"][a]["found"]:
                    print "2",self.xmlFile
                    logging.info(str(i) + " " + str(a) + " not found")
                    return False
        return True

    def parse(self, xmlFile=None):
        """ Method to parse the xml file for dtd information

            Parameters
            ----------
            xmlFile : str
                The name of the xml file to search, does not need to be
                specified if the file was given in the constructor.
                Default : None

            Returns
            -------
            None
        """
        # parse the dtd and generate the hierarchy
        if self.xmlFile is None:
            if xmlFile is None:
                raise Exception("No xml file to parse")
            self.xmlFile = xmlFile
        f = open(self.xmlFile, 'r')
        lines = f.readlines()
        f.close()
        for line in lines:
            # treat the different entries appropriately
            if "<!ELEMENT" in line:
                en = line.split()
                name = en[1]
                if en[1].endswith("_AT"):
                    self.at = "_" + en[1]
                elif self.at is not None:
                    name += self.at
                self.entities[name] = {"found" : False,
                                       "attrib": {}}
            elif "<!ATTLIST" in line:
                at = line.split()
                values = at[3].replace(")", "")
                values = values.replace("(", "")
                values = values.split("|")
                name = at[1]
                if self.at is not None:
                    name += self.at
                self.entities[name]["attrib"][at[2]] = {"found" : False,
                                                        "values": values}
            elif "]>" in line:
                break

    def check(self, name, attrib=None, value=None):
        """ Method to check a node for validity. Validity includes correct name
            and data type.

            Parameters
            ----------
            name : str
                The name of the node being checked

            attrib : str
                The attribute of the node being checked, if any.
                Default: None

            value : str
                The type of the attribute being checked (e.g. bt.INT)
                Default: None
        """
        # check a node for validity
        try:
            # note that the node has been found
            self.entities[name]["found"] = True
            # if there is an attribute specified then check it too
            # if the attribute was not expected just print a note to the screen
            if attrib is not None:
                try:
                    if not value in self.entities[name]["attrib"][attrib]["values"] \
                       and not "ANY" in self.entities[name]["attrib"][attrib]["values"]:
                        raise Exception("DTDParser.check: Value %s for attribute %s is not a valid entry (attribute = %s) (file %s)" % (value, name, attrib, self.xmlFile))
                    self.entities[name]["attrib"][attrib]["found"] = True
                except KeyError:
                    logging.info("Attribute %s for %s not listed in DTD, malformed xml detected (%s)" %
                                 (attrib, name, self.xmlFile))
                    logging.info("Inconsistency between dtd and xml detected, continuing")
                except:
                    logging.info("Unknown error encountered while parsing attribute %s for %s (%s)" %
                                 (attrib, name, self.xmlFile))
                    raise
        except KeyError:
            logging.info("Data member %s is not a member of the dtd, xml inconsistent with definition (%s)" %
                         (name, self.xmlFile))
        except:
            raise

    def checkAttribute(self, name, attrib, value=None):
        """ Method to check an attribute for validity. Validity includes correct
            name and data type.

            Parameters
            ----------
            name : str
                The name of the node being checked

            attrib : str
                The attribute of the node being checked, if any.

            value : str
                The type of the attribute being checked (e.g. bt.INT)
                Default: None
        """
        # check an attribute for validity
        try:
            if not value in self.entities[name]["attrib"][attrib]["values"] \
               and not "ANY" in self.entities[name]["attrib"][attrib]["values"]:
                raise Exception("DTDParser.checkAttributes: Value %s for attribute %s is not a valid entry (file %s)" %
                                (value, name, self.xmlFile))
            self.entities[name]["attrib"][attrib]["found"] = True
        except KeyError:
            logging.info("Attribute %s not listed in DTD, malformed xml detected (%s)" %
                         (attrib, self.xmlFile))
            logging.info("Inconsistency between dtd and xml detected, continuing")
        except:
            logging.info("Unknown error encountered while parsing attribute %s (%s)" %
                         (attrib, self.xmlFile))
            raise
