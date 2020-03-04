""" .. _LineData-api:

    **LineData** --- Extended spectral line metadata.
    -------------------------------------------------

    This module defines the LineData class.
"""

from admit.util.Line import Line


class LineData(Line):
    """ Class for holding information on a specific spectral line, expanding on that of the Line
        base class.

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

        mass : int
            Rough mass of the molecule (H=1, C=12, etc.).
            Default: 0.

        plain : str
            A human redable version of the chemical formula.
            Default: "".

        isocount : int
            A count of the number of non-standard isotopes in the molecule. For example the standard
            for carbon is 12C and 13C would be the non-standard isotope.
            Default: 0.

        chans : two element list
            List of the starting and ending channels of the line.
            Default: [0, 0].

        freqs : two element list
            List of the starting and ending frequencies of the line.
            Default: [0.0, 0.0].

        peakintensity : float
            The peak intensity of the line in units from the input data.
            Default: 0.0.

        peakrms : float
            The S/N of the peak of the line.
            Default: 0.0.

        fwhm : float
            Full width half maximum of the line.
            Default: 0.0.

        noise : float
            The rms noise of the spectrum.
            Default: 0.0.

        hfnum : int
            Hyperfine identifier from the Tier1 database.
            Default: 0 (no hyperfines).

        peakoffset : float
            The offset of the peak of the line from the vlsr.
            Default: 0.0.

        velocity : float
            The velocity of the line (offset + vlsr).
            Default: 0.0.

        force : bool
            If True then the user forced the identification via the force keyword in LineID, if
            False then the id was generated by LineID.
            Default: False.
    """
    def __init__(self, **keyval):
        self.mass = 0
        self.plain = ""
        self.isocount = 0
        self.chans = [0, 0]
        self.freqs = [0.0, 0.0]
        self.peakintensity = 0.0
        self.peakrms = 0.0
        self.fwhm = 0.0
        self.noise = 0.0
        self.hfnum = 0
        self.velocity = 0.0
        self.peakoffset = 0.0
        self.force = False
        Line.__init__(self)
        self.setkey(keyval)

    def __str__(self):
        return "%s %g %f" % (self.uid,self.energies[1],self.linestrength)

    def setkey(self, name="", value=""):
        """ Method to set the key-value pairs for the class. It treats the chans and freqs keywords
            specially, making sure that the pairs of numbers are properly ordered. All other keys
            and values are passed directly to the Line superclass setkey.

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
            for k, v in name.items():
                if k == "freqs" or k == "chans":
                    v.sort()
                    name[k] = v
        elif name == "freqs" or name == "chans":
            if len(value) != 2:
                raise
            value.sort()
        Line.setkey(self,name, value)

    def getstart(self):
        """ Method to get the starting channel number.

            Parameters
            ----------
            None

            Returns
            -------
            Int containing the starting channel number

        """
        return self.chans[0]

    def getend(self):
        """ Method to get the ending channel number.

            Parameters
            ----------
            None

            Returns
            -------
            Int containing the ending channel number

        """
        return self.chans[1]

    def setstart(self, chan):
        """ Method to set the starting channel number.

            Parameters
            ----------
            chan : int
                The starting channel number to set

            Returns
            -------
            None

        """
        self.chans[0] = chan

    def setend(self, chan):
        """ Method to set the ending channel number.

            Parameters
            ----------
            chan : int
                The ending channel number to set

            Returns
            -------
            None

        """
        self.chans[1] = chan

    def getfstart(self):
        """ Method to get the starting frequency.

            Parameters
            ----------
            None

            Returns
            -------
            Float containing the starting frequency

        """
        return self.freqs[0]

    def getfend(self):
        """ Method to get the ending frequency.

            Parameters
            ----------
            None

            Returns
            -------
            Float containing the ending frequency

        """
        return self.freqs[1]

    def setfstart(self, freq):
        """ Method to set the starting frequency.

            Parameters
            ----------
            chan : int
                The starting frequency to set

            Returns
            -------
            None

        """
        self.freqs[0] = freq

    def setfend(self, freq):
        """ Method to set the ending frequency.

            Parameters
            ----------
            chan : int
                The ending frequency to set

            Returns
            -------
            None

        """
        self.freqs[1] = freq

    def setchans(self, chans):
        """ Method to set the channel range for the line.

            Parameters
            ----------
            chans : list
                Two element list of the channel range for the line

            Returns
            -------
            None

        """
        self.chans[0] = min(chans)
        self.chans[1] = max(chans)

    def setfreqs(self, freqs):
        """ Method to set the frequency range for the line.

            Parameters
            ----------
            chans : list
                Two element list of the frequency range for the line

            Returns
            -------
            None

        """
        self.freqs[0] = min(freqs)
        self.freqs[1] = max(freqs)

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
        # treat a few specific ones specially
        if key == "El":
            return self.getlowerenergy()
        if key == "Eu":
            return self.getupperenergy()
        if key == "startchan":
            return self.getstart()
        if key == "endchan":
            return self.getend()
        return Line.getkey(self, key)

    def converttoline(self):
        """ Method to convert the contents of the LineData object to a Line Object

            Parameters
            ----------
            None

            Returns
            -------
            Line object populated with the relevant data from this LineData object

        """
        line = Line()
        for item in line.__dict__:
            if item.startswith("_"):
                continue
            line.setkey(item,self.getkey(item))
        return line
