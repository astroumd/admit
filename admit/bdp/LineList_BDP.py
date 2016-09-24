""" **LineList_BDP** --- LineID_AT data (line information and spectra).
    -------------------------------------------------------------------

    This module defines the LineList_BDP class.
"""
# system imports
import numpy as np
import copy

# ADMIT imports
from admit.bdp.Table_BDP import Table_BDP
from admit.bdp.Image_BDP import Image_BDP
from admit.util.Table import Table
from admit.util import Spectrum
import admit.util.utils as utils
from admit.util import LineData


class LineList_BDP(Table_BDP, Image_BDP):
    """ LineList BDP class.

        This class contains a list of spectral lines identified by the LineID
        AT. The columns in the table are: fullname (name of the molecule "U"
        for unknown), formula (chemical formula), frequency (rest frequency in
        GHz), uid (unique identifier consisting of the formula and rest
        frequency), transition (molecular, vibrational or electronic
        transition), velocity (relative to the rest velocity), El (lower state
        energy in K), Eu (upper state energy in K), linestrength (line
        strength of the transition in Debye^2), peakintensity (peak intensity
        of the transition in Jy/bm), peakoffset (offset of the peak from rest
        in km/s), fwhm (full width half max of the line in km/s), startchan
        (starting channel in the spectral window), endchan (ending channel in
        the spectral window), and sigma (intensity of the line relative to the
        noise level).

        Parameters
        ----------
        xmlFile : str
            Output XML file name.

        keyval : dict
            Dictionary of keyword:value pairs.

        Attributes
        ----------
        table : Table
            Instance of the Table class to hold the spectral line information.

        veltype : str
            Velocity definition used for the spectrum.
            Default: "vlsr"

        ra : str
            The RA of where the spectrum was taken.
            Default: ""

        dec : str
            The declination of where the spectrum was taken.
            Default: ""

        spectra : Table
            Instance of the Table class to hold spectra.

    """

    def __init__(self, xmlFile=None, **keyval):
        Table_BDP.__init__(self, xmlFile)
        Image_BDP.__init__(self, xmlFile)
        self.veltype = "vlsr"
        self.ra = ""
        self.dec = ""
        self.table.setkey("columns", utils.linelist_columns)
        self.table.setkey("units", utils.linelist_units)
        self.table.description="Identified Spectral Lines"
        self.table.data = np.array([], dtype=object)
        self.spectra = Table()
        self.spectra.setkey("columns", ["channel", "frequency", "intensity",
                                        "mask", "continuum", "noise"])
        self.spectra.setkey("units", ["", "GHz", "", "", "", ""])
        self.setkey(keyval)
        self._version= "0.2.0"

    def addSpectrum(self, spectrum, name, replace=False):
        """ Method to add a spectrum to the BDP

            Parameters
            ----------
            spectrum : Spectrum object
                The spectrum to add to the BDP

            name : str
                The name of the spectrum to add (e.g. cubestats)

            replace : bool
                If True replace the spectrum with the existing name.

            Returns
            -------
            None

        """
        # turn the data into a table plane
        contin = spectrum.contin(masked=False)
        if contin is None:
            contin = np.zeros(len(spectrum))
        if isinstance(contin, int) or isinstance(contin, float):
            contin = np.array([contin] * len(spectrum))
        noise = np.array([spectrum.noise()] * len(spectrum))
        data = np.column_stack((spectrum.chans(False), spectrum.freq(False),
                                spectrum.spec(csub=False, masked=False),
                                spectrum.mask(), contin, noise))

        # see if a plane already exists with the given name
        if name in self.spectra.planes:
            if replace:
                print "NOT IMPLEMENTED YET"
                #self.spectra.replace(name, spectrum)
                return
            else:
                raise Exception("Name %s already exists in Table." % (name))
        # if this is the first one
        if self.spectra.shape()[0] == 0:
            self.spectra.addPlane(data, name)
            return
        chans = []
        chans.append(self.spectra.getColumnByName("channel", typ=np.int32))
        # since all planes must have the same shape (numpy restriction) then make sure that they
        # all have the same shape before trying to combine them
        if len(chans[0]) == len(spectrum.chans()) and chans[0][0] == spectrum.chans(False)[0] and \
           chans[0][1] == spectrum.chans()[-1]:
            self.spectra.addPlane(data, name)
            return
        # they are not the same shape (length really) then the shorter ones need to be padded at
        # one or both ends
        # check for alignment of the channel axis
        prependspec = int(max(0, chans[0][0] - spectrum.chans(False)[0]))
        appendspec = int(max(0, spectrum.chans(False)[-1] - chans[0][-1]))
        prependdata = int(max(0, spectrum.chans(False)[0] - chans[0][0]))
        appenddata = int(max(0, chans[0][-1] - spectrum.chans(False)[-1]))

        finaldata = {}
        # if the plane being added is smaller then pad it by taking the entries from the main table
        # setting the spectra to 0.0 and set the mask to True (bad data)
        if appenddata != 0 or prependdata != 0:
            temp = self.spectra.getPlane(0)
            pps = temp[:prependdata]
            pps[:, 2] = 0.0
            pps[:, 3] = True
            pps[:, 4] = 0.0
            if appenddata != 0:
                aps = temp[-appenddata:]
            else:
                aps = temp[:0]
            aps[:, 2] = 0.0
            aps[:, 3] = True
            aps[:, 4] = 0.0

            finaldata[name] = np.vstack((pps, data, aps))
        else:
            finaldata[name] = data

        # if the main table is smaller then pad all planes by taking the entries from the new plane
        # setting the spectra to 0.0 and set the mask to True (bad data)
        if prependspec != 0 or appendspec != 0:
            spec = {}
            if len(self.spectra.shape()) == 2:
                spec[self.spectra.planes[0]] = copy.deepcopy(self.spectra.getPlane(0))
            else:
                for i in range(self.spectra.shape()[2]):
                    spec[self.spectra.planes[i]] = copy.deepcopy(self.spectra.getPlane(i))
            self.spectra.clear()
            pps = data[:prependspec]
            pps[:, 2] = 0.0
            pps[:, 3] = True
            pps[:, 4] = 0.0
            if appendspec != 0:
                aps = data[-appendspec:]
            else:
                aps = data[:0]
            aps[:, 2] = 0.0
            aps[:, 3] = True
            aps[:, 4] = 0.0
            for sname, values in spec.iteritems():
                finaldata[sname] = np.vstack((pps, values, aps))

        # put it all together
        for pname, plane in finaldata.iteritems():
            self.spectra.addPlane(plane, pname)

    def getSpectraNames(self):
        """ Method to get the names of the spectra

            Parameters
            ----------
            None

            Returns
            -------
            List of strings containing the names

        """
        return self.spectra.planes

    def getSpectrum(self, name):
        """ Method to get a specific spectrum by name

            Parameters
            ----------
            name : str
                The name of the spectrum to get

            Returns
            -------
            Spectrum instance containing the spectrum

        """
        if name not in self.spectra.planes:
            raise Exception("Spectrum %s does not exist." % (name))
        plane = self.spectra.planes.index(name)
        chans = self.spectra.getColumnByName("channel", plane, np.int32)
        freq = self.spectra.getColumnByName("frequency", plane, np.float64)
        spec = self.spectra.getColumnByName("intensity", plane, np.float64)
        mask = self.spectra.getColumnByName("mask", plane, np.bool)
        noise = self.spectra.getColumnByName("noise", plane, np.float64)[0]
        contin = self.spectra.getColumnByName("continuum", plane, np.float64)
        spectrum = Spectrum(spec=spec, freq=freq, chans=chans, mask=mask,
                            contin=contin, noise=noise)
        return spectrum

    def addRow(self, row):
        """ Method to add a row to the table

            Parameters
            ----------
            row : LineData object
                LineData object containing the data

            Returns
            -------
            None

        """
        data = []
        # build the row from the data
        for col in utils.linelist_columns:
            data.append(row.getkey(col))
        self.table.addRow(data)

    def __len__(self):
        return len(self.table)

    def getall(self):
        """ Method to get all rows from the table as a list of LineData objects

            Parameters
            ----------
            None

            Returns
            -------
            List of LineData objects, one for each row in the table.

        """
        planes = self.getSpectraNames()
        tempspec = None
        if len(planes) > 0:
            tempspec = self.getSpectrum(planes[0])
        rows = []
        for i in range(len(self)):
            row = self.table.getRow(i)
            ld = LineData(name=row[self.table.columns.index("name")],
                        uid=row[self.table.columns.index("uid")],
                        transition=row[self.table.columns.index("transition")],
                        energies=[row[self.table.columns.index("El")], row[self.table.columns.index("Eu")]],
                        linestrength=float(row[self.table.columns.index("linestrength")]),
                        frequency=float(row[self.table.columns.index("frequency")]),
                        blend=int(row[self.table.columns.index("blend")]),
                        chans=[row[self.table.columns.index("startchan")], row[self.table.columns.index("endchan")]],
                        formula=row[self.table.columns.index("formula")],
                        velocity=row[self.table.columns.index("velocity")],
                        peakintensity=row[self.table.columns.index("peakintensity")],
                        peakoffset=row[self.table.columns.index("peakoffset")],
                        fwhm=row[self.table.columns.index("fwhm")],
                        peakrms=row[self.table.columns.index("peakrms")],
                        force=row[self.table.columns.index("force")])
            if tempspec is not None:
                frqs = [tempspec.getfreq(row[self.table.columns.index("startchan")]),
                        tempspec.getfreq(row[self.table.columns.index("endchan")])]
                frqs.sort()
                ld.setkey("freqs", frqs)
            rows.append(ld)
        return rows

