""" .. _Line-api:

    **Line** --- Spectral line metadata.
    ------------------------------------

    This module defines the Line class for LINE entries in BDPs.
"""
# system imports
import xml.etree.cElementTree as et

# ADMIT imports
import bdp_types as bt
from UtilBase import UtilBase


class Line(UtilBase):
    """ Class for holding information on a specific spectral line.

        Parameters
        ----------
        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        name : str
            Name of the molecule/atom.
            Default: "".

        uid : str
            Unique identifier for the transition.
            Default: "".

        formula : str
            The chemical formula.
            Default: "".

        transition : str
            The transition/quantum number information.
            Default: "".

        energies : 2 element list
            List of the lower and upper state energies of the transition.
            Default: [0.0, 0.0].

        energyunits : str
            Units of the upper/lower state energy.
            Default: K.

        linestrength : float
            The line strength of the transition.
            Default: 0.0.

        lsunits : str
            The units of the line strength.
            Default: "Debye^2".

        frequency : float
            The frequency of the transition.
            Default: 0.0.

        funits : str
            The units of the frequency.
            Default: "GHz".

        blend : int
            If this molecule is blended with others. Value of 0 means no blending
            any other value gives the index of the blend.
            Default: 0 (no blending).
    """
    def __init__(self, **keyval):
        self.name = ""
        self.uid = ""
        self.formula = ""
        self.transition = ""
        self.energies = [0.0, 0.0]
        self.energyunits = "K"
        self.linestrength = 0.0
        self.lsunits = "Debye^2"
        self.frequency = 0.0
        self.funits = "GHz"
        self.blend = 0
        UtilBase.__init__(self, **keyval)

    def setupperenergy(self, value):
        """ Method to set the upper state energy.

            Parameters
            ----------
            value : float
                The value to set the upper state energy to.

            Returns
            -------
            None
        """
        if isinstance(value, float) :
            self.energies[1] = value
        elif isinstance(value, int) :
            self.energies[1] = float(value)
        else :
            raise Exception("Energy must be a number")

    def setlowerenergy(self, value):
        """ Method to set the lower state energy.

            Parameters
            ----------
            value : float
                The value to set the lower state energy to.

            Returns
            -------
            None
        """
        if isinstance(value, float) :
            self.energies[0] = value
        elif isinstance(value, int) :
            self.energies[0] = float(value)
        else :
            raise Exception("Energy must be a number")

    def getlowerenergy(self) :
        """ Method to get the lower state energy.

            Parameters
            ----------
            None

            Returns
            -------
            Float of the lower state energy.

        """
        return self.energies[0]

    def getupperenergy(self):
        """ Method to get the upper state energy.

            Parameters
            ----------
            None

            Returns
            -------
            Float of the upper state energy.

        """
        return self.energies[1]

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
                        if k == "energies" and not isinstance(v, list) and len(v) != 2:
                            raise Exception("Energies must be a list in the format [lower, upper], use setupperenergy or setlowerenergy to set them individually.")
                        setattr(self, k, v)
                    else:
                        raise Exception("Cannot change data type for %s, expected %s but got %s" % (k, str(type(getattr(self, k))), str(type(v))))
                else:
                    raise Exception("Invalid key given to Line class: %s" % (k))
        elif not name == "":
            if hasattr(self, name):
                if type(value) == type(getattr(self, name)):
                    if name == "energies" and not isinstance(value, list) and len(value) != 2:
                        raise Exception("Energies must be a list in the format [lower, upper], use setupperenergy or setlowerenergy to set them individually.")
                    setattr(self, name, value)
                else:
                    raise Exception("Cannot change data type for %s, expected %s but got %s" % (name, str(type(getattr(self, name))), str(type(value))))
            else:
                raise Exception("Invalid key given to Line class: %s" % (name))
        else:
            raise Exception("Invalid name parameter given, it must be a string or a dictionary of keys:values.")

    def isequal(self, line):
        """ Experimental method to compare 2 line classes

            Parameters
            ----------
            line : Line
                The class to compare this one to.

            Returns
            -------
            Boolean whether or not the two classes contain the same data.

        """
        try:
            for i in self.__dict__:
                if cmp(getattr(self, i), getattr(line, i)) != 0:
                    return False
        except:
            return False
        return True
