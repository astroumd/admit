"""
    .. _UTIL-base-api:

    **UtilBase** --- Base for all ADMIT utilities.
    ----------------------------------------------

    This module defines the UtilBase class.
"""

import bdp_types as bt
import xml.etree.cElementTree as et


class UtilBase(object):
    """ Defines the utility base class. All utility classes (e.g. Table, Line, etc)
        must inherit from this class. The class has the basic infrastructure for
        printing the class contents and setting variables. Utility classes do not
        have to have a write method as it is dynamically done by the xml writer.

        Parameters
        ----------
        keyval : dict
            Dictionary containing the keyword value pairs of all arguments.

        Attributes
        ----------
        _type : str
            String containing the type of the class.

        _order : list
            List containing the order to write out the data in, generated on
            initialization.

    """
    def __init__(self, **keyval):
        self._type = self.__class__.__name__
        self._order = []
        self.setkey(keyval)
        for i in self.__dict__:
            if i == "_type" or i == "_order":
                continue
            self._order.append(i)

    def __str__(self):
        print bt.format.BOLD + bt.color.GREEN + " " + self._type + ":" + bt.format.END
        for i, j in self.__dict__.iteritems():
            print bt.format.BOLD + i + ": " + bt.format.END + str(j)
        return ""

    def getkey(self, key):
        """ Method to get a data member by name

            Parameters
            ----------
            key : str
                The name of the data member to return

            Returns
            -------
            various, the contents of the requested item

        """
        if hasattr(self, key):
            return getattr(self, key)
        raise Exception("Class %s has no member named %s" % (self.__class__, key))

    def setkey(self, name="", value=""):
        """
            set keys, two styles are possible:

            1. name = {key:val}            e.g. **setkey({"a":1})**

            2. name = "key", value = val     e.g. **setkey("a", 1)**

            This method checks the type of the keyword value, as it must
            remain the same. Also new keywords cannot be added.

            Parameters
            ----------

            name : dictionary or string
                Dictionary of keyword value pais to set or a string with the name
                of a single key

            value : any
                The value to change the keyword to

            Returns
            -------
            None
        """
        if isinstance(name, dict):
            for k, v in name.iteritems():
                if hasattr(self, k):
                    if type(v) == type(getattr(self, k)):
                        setattr(self, k, v)
                    else:
                        raise Exception("Cannot change data type for %s, expected %s but got %s"
                                        % (k, str(type(getattr(self, k))), str(type(v))))
                else:
                    raise Exception("Invalid key given to %s class: %s" % (self._type, k))
        elif not name == "":
            if hasattr(self, name):
                if type(getattr(self, name)) == type(value):
                    setattr(self, name, value)
                else:
                    raise Exception("Cannot change data type for %s, expected %s but got %s"
                                    % (name, str(type(getattr(self, name))), str(type(value))))
            else:
                raise Exception("Invalid key given to %s class: %s" % (self._type, name))
        else:
            raise Exception("Invalid name parameter given, it must be a string or a dictionary of keys:values.")
