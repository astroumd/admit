""" .. _SpectrumIngest-api:

    **SpectrumIngest** --- Converts non-ADMIT spectral data to ADMIT format.
    ------------------------------------------------------------------------

    This module defines the SpectrumIngest class.
"""

# system imports
import numpy as np
import copy
import os

# ADMIT imports
from admit.bdp.CubeSpectrum_BDP import CubeSpectrum_BDP
from admit.util.AdmitLogging import AdmitLogging as logging
from admit.util import Spectrum
from admit.util.Table import Table
from admit.util.Image import Image
from admit.util import APlot
import admit.util.utils as utils
import admit


class SpectrumIngest(object):
    """ This class is used to convert foreign data (either files or arrays) into a CubeSpectrum_BDP
        suitable for use as an input to LineID_AT. If files are used then then the columns
        containing the frequency and the intensity must be given (channel numbers are optional). Any
        number of files can be given, but all spectra must have the same length as they are assumed
        to come from the same data source. Blank lines and lines starting with a comment '#' will be
        skipped, additionally any line with too few columns will be skipped. If arrays are used an
        input then both the frequency and intensity must be specified (the channel numbers are
        optional). Both lists and numpy arrays are accepted as inputs. Multidimmensional arrays are
        supported with the following parameters:

        + A single frequency list can be given to cover all input spectra, otherwise the shape
          of the frequency array must match that of the spectra
        + A single channel list can be given to cover all input spectra, otherwise the shape
          of the channel array must match that of the spectra
        + All spectra must have the same length

        If a channel array is not specified then one will be constructed with the following
        parameters:

        + The channel numbers will start at 0 (casa convention)
        + The first entry in the spectrum will be considered the first channel, regardless of
          whether the frequency array increases or decreases.

        The convert method will return a single CubeSpectrum_BDP instance holding all input spectra
        along with an image of each.

        Parameters
        ----------
        None

        Attributes
        ----------
        chan : array
            An array holding the channel numbers for the data, multidimmensional arrays are
            supported.
            Default: None.

        chancol : int
            The column of the input file(s) that corresponds to the channel listing. Column numbers
            are 1 based.
            Default: -1.

        freq : array
            An array holding the frequencies for the data, multidimmensional arrays are supported.
            Default: None.

        freqcol : int
            The column of the input file(s) that corresponds to the frequency listing. Column
            numbers are 1 based.
            Default: -1.

        spec : array
            An array holding the intesities of the data, multidimmensional arrays are supported.
            Default: None.

        speccol : int
            The column of the input file(s) that corresponds to the intensity listing. Column
            numbers are 1 based.
            Default: -1.

        file : list or str
            A single file name or a list of file names to be read in for spectra.
            Default: None.

        seperator : str
            The column separator for reading in the data files.
            Default: None (any whitespace).

        length : int
            Internal tracking of the length of the spectra.
    """
    def __init__(self):
        self.chan = None
        self.chancol = -1
        self.freq = None
        self.freqcol = -1
        self.velocity = None
        self.velcol = -1
        self.spec = None
        self.speccol = -1
        self.file = []
        self.separator = None
        self.restfreq = None
        self.vlsr = None
        self.length = 0

    def getfile(self, file):
        """ Method to read in a file and convert it to a Spectrum. Columns must already have been
            specified.

            Parameters
            ----------
            file : str
                Name of the file to read in

            Returns
            -------
            Spectrum instance containing the data read in from the file

        """
        # do some consistency and integrity checking
        if self.freqcol is None and self.velcol is None:
            raise Exception("Either the frequency column or velocity column must be specified.")
        if not isinstance(self.chancol, int):
            raise Exception("chan parameter must be an int.")
        if not isinstance(self.freqcol, int) and self.freqcol is not None:
            raise Exception("freq parameter must be an int.")
        if not isinstance(self.velcol, int) and self.velcol is not None:
            raise Exception("velocity parameter must be an int.")
        if not isinstance(self.speccol, int):
            raise Exception("spec parameter must be an int.")
        #if self.freqcol < 0 and self.freqcol is not None:
        #    raise Exception("The frequency column must be specified (i.e. freq=1)")
        if self.speccol < 0:
            raise Exception("The spectral column must be specified (i.e. spec=1)")
        print self.velcol
        if self.velcol >= 0:
            if self.restfreq is not None:
                if not isinstance(self.restfreq, float) and not isinstance(self.restfreq, int):
                    raise Exception("Restfreq must be a float.")
            else:
                raise Exception("Restfreq must be specified.")
            if self.vlsr is None:
                print "vlsr was not specified, assuming it is 0.0"
                self.vlsr = 0.0
            elif not isinstance(self.vlsr, float) and not isinstance(self.vlsr, int):
                raise Exception("vlsr must be a float")
        # find out the minimum number of columns to expect
        mincol = max(self.freqcol, self.chancol, self.speccol)

        # open the file and read it in
        fl = open(file, 'r')
        lines = fl.readlines()
        fl.close()

        # track line that are skipped for various reasons
        skipped = 0
        comments = 0
        blank = 0

        freq = []
        spec = []
        chan = []

        # go through each line
        for line in lines:
            # if the line is blank
            if len(line) < 1:
                blank += 1
                continue

            # if the line is a comment
            if line.startswith("#"):
                comments += 1
                continue

            # split the line up
            data = line.split(self.separator)

            # if there are not enough columns
            if len(data) < mincol:
                skipped += 1
                continue

            # add the data to the arrays
            if self.velcol >= 0:
                freq.append(float(data[self.velcol - 1]))
            else:
                freq.append(float(data[self.freqcol - 1]))
            spec.append(float(data[self.speccol - 1]))
            if self.chancol > 0:
                chan.append(int(data[self.chancol - 1]))
        if self.velcol >= 0:
            for i, frq in enumerate(freq):
                freq[i] = self.restfreq + utils.veltofreq(self.vlsr - frq, self.restfreq)

        # if the was no channel column the generate it
        if len(chan) == 0:
            chan = range(len(spec))

        # report what was found
        print "Imported %i lines from file %s" % (len(spec), file)
        if blank > 0:
            print "Skipped %i blank lines from file %s" % (blank, file)
        if skipped > 0:
            print "Skipped %i lines with too few columns from file %s" % (skipped, file)
        if comments > 0:
            print "Skipped %i commented lines from file %s" % (comments, file)
        if self.length == 0:
            self.length = len(spec)
        else:
            # if this spectrum is not the same length of the others
            if self.length != len(spec):
                raise Exception("Not all input spectra are the same length.")

        # convert to a Spectrum instance
        return Spectrum(spec=spec, freq=freq, chans=chan)

    def convert(self, chan=None, freq=None, velocity=None, spec=None, file=None, separator=None, 
                restfreq=None, vlsr=None):
        """ Method to convert input data (either files or arrays) into a CubeSpectrum_BDP. If files
            are used then then the columns containing the frequency and the intensity must be given
            (channel numbers are optional). Any number of files can be given, but all spectra must
            have the same length as they are assumed to come from the same data source. Blank lines
            and lines starting with a comment '#' will be skipped, additionally any line with too
            few columns will be skipped. If arrays are used an input then both the frequency and
            intensity must be specified (the channel numbers are optional). Both lists and numpy
            arrays are accepted as inputs. Multidimmensional arrays are supported with the following
            parameters:

            + A single frequency list can be given to cover all input spectra, otherwise the shape
              of the frequency array must match that of the spectra
            + A single channel list can be given to cover all input spectra, otherwise the shape
              of the channel array must match that of the spectra
            + All spectra must have the same length

            If a channel array is not specified then one will be constructed with the following
            parameters:

            + The channel numbers will start at 0 (casa convention)
            + The first entry in the spectrum will be considered the first channel, regardless of
              whether the frequency array increases or decreases.

            Additionally, if there is velocity axis, but no frequency axis, a frequency axis can
            be constructed by specifying a rest frequency (restfreq), and vlsr.

            The convert method will return a single CubeSpectrum_BDP instance holding all input spectra
            along with an image of each.

            Parameters
            ----------
            chan : array or int
                An array holding the channel numbers for the data, multidimmensional arrays are
                supported. If an integer is specified then it is the number of the column
                in the file which contains the channel numbers, column numbers are 1 based.
                Default: None

            freq : array
                An array holding the frequencies for the data, multidimmensional arrays are
                supported. If an integer is specified then it is the number of the column
                in the file which contains the frequencies, column numbers are 1 based.
                Default: None

            velocity : array
                An array holding the velocity for the data, multidimmensional arrays are
                supported. If an integer is specified then it is the number of the column
                in the file which contains the velcoties, column numbers are 1 based. If this
                parameter is specified then restfreq and vlsr must also be specified.
                Default: None

            spec : array
                An array holding the intesities of the data, multidimmensional arrays are supported.
                If an integer is specified then it is the number of the column in the file which
                contains the intensities, column numbers are 1 based.
                Default: None

            file : list or str
                A single file name or a list of file names to be read in for spectra.
                Default: None

            separator : str
                The column separator for reading in the data files.
                Default: None (any whitespace)

            restfreq : float
                The rest frequency to use to convert the spectra from velocity to frequency units.
                The rest frequency is in GHz.
                Default: None (no conversion done)

            vlsr : float
                The reference velocity for converting a velocity axis to frequency. The units are
                km/s. If this is not set then it is assumed that the vlsr is 0.0.
                Default: None

            Returns
            -------
            CubeSpectrum_BDP instance containing all of the inpur spectra.

        """
        self.restfreq = restfreq
        self.vlsr = vlsr

        # if a string was given as the file name then turn it into a list so it can be iterated over
        if isinstance(file, str):
            self.file = [file]
        else:
            self.file = file
        # do some error checking
        if isinstance(chan, np.ndarray) or isinstance(chan, list):
            if isinstance(chan, list):
                self.chan = np.array(chan)
            else:
                self.chan = copy.deepcopy(chan)
            self.chancol = -1
        elif isinstance(chan, int):
            self.chancol = chan
            self.chan = None
        else:
            self.chancol = -1
            self.chan = None
        if isinstance(freq, np.ndarray) or isinstance(freq, list):
            if isinstance(freq, list):
                self.freq = np.array(freq)
            else:
                self.freq = copy.deepcopy(freq)
            self.freqcol = -1
        elif isinstance(freq, int):
            self.freqcol = freq
            self.freq = None
        else:
            self.freqcol = -1
            self.freq = None
        if isinstance(velocity, np.ndarray) or isinstance(velocity, list):
            if isinstance(velocity, list):
                self.freq = np.array(velocity, dtype=np.float)
            else:
                self.freq = velocity.astype(np.float)
            for i, frq in enumerate(self.freq):
                self.freq[i] = self.restfreq + utils.veltofreq(frq - self.vlsr, self.restfreq)
            self.freqcol = -1
        elif isinstance(velocity, int):
            self.velcol = velocity
            self.velocity = None
        else:
            self.velcol = -1
            self.velocity = None
        if isinstance(spec, np.ndarray) or isinstance(spec, list):
            if isinstance(spec, list):
                self.spec = np.array(spec)
            else:
                self.spec = copy.deepcopy(spec)
            self.speccol = -1
        elif isinstance(spec, int):
            self.speccol = spec
            self.spec = None
        else:
            self.speccol = -1
            self.spec = None
        if isinstance(separator, str):
            self.separator = separator
        spectra = []
        # read in the data from any files
        if self.file:
            for fl in self.file:
                spectra.append(self.getfile(fl))
        else:
            # convert the input arrays
            singlefreq = False
            singlechan = False
            havechan = False
            # make sure they have the same shape or that the frequency array is 1D
            if self.spec.shape != self.freq.shape:
                if len(self.spec.shape) == 1 and len(self.freq.shape) != 1:
                    raise Exception("Frequency axis and spectral axis do not have the same shape.")
                else:
                    singlefreq = True
            # make sure they have the same shape or that the channel array is 1D
            if self.chan:
                havechan = True
                if self.spec.shape != self.chan.shape:
                    if len(spec.shape) == 1 and len(self.chan.shape) != 1:
                        raise Exception("Channel axis and spectral axis do not have the same shape.")
                    else:
                        singlechan = True
            # if the arrays are more than 1D, then go through each
            if len(self.spec.shape) > 1:
                for i in range(self.spec.shape[0]):
                    spec = self.spec[i]
                    if not havechan:
                        chan = np.arange(len(spec))
                    elif singlechan:
                        chan = self.chan
                    else:
                        chan = self.chan[i]
                    if singlefreq:
                        freq = self.freq
                    else:
                        freq = self.freq[i]
                    spectra.append(Spectrum(spec=spec, freq=freq, chans=chan))
            else:
                # construct the channel array if needed
                if not havechan:
                    self.chan = np.arange(len(self.spec))
                spectra.append(Spectrum(spec=self.spec, freq=self.freq, chans=self.chan))

        first = True
        images = {}

        # make images from the spectra
        for i, spec in enumerate(spectra):
            data = (spec.chans(masked=False), spec.freq(masked=False),
                    spec.spec(csub=False, masked=False))
            if first:
                table = Table(columns=["channel", "frequency", "flux"],
                              units=["number", "GHz", "Unknown"], data=np.column_stack(data),
                              planes=["0"])
                first = False
            else:
                table.addPlane(np.column_stack(data), "%i" % i)
            myplot = APlot(ptype=admit.PlotControl.PNG, pmode=admit.PlotControl.BATCH,
                                 abspath=os.getcwd())
            myplot.plotter(spec.freq(masked=False), [spec.spec(csub=False, masked=False)],
                           title="Spectrum %i" % i, figname="fig_%i" % i, xlab="Frequency",
                           ylab="Intensity", thumbnail=True)
            # Why not use p1 as the key?
            images["fig%i" % i] = myplot.getFigure(figno=myplot.figno, relative=True)
        image = Image(images=images, description="Spectra")
        # construct the BDP
        bdp = CubeSpectrum_BDP(image=image, table=table)

        return bdp
