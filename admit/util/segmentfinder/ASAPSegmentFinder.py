""" .. _asapsegment:

    ASAPSegmentFinder --- Finds segments of emission within a spectrum.
    -------------------------------------------------------------------

    This module defines the class for spectral line segment detection.
"""
#*******************************************************************************
# ALMA - Atacama Large Millimeter Array
# Copyright (c) ATC - Astronomy Technology Center - Royal Observatory Edinburgh, 2011
# (in the framework of the ALMA collaboration).
# All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#*******************************************************************************

import os
import numpy as np
import copy
import math
import numpy.ma as ma

# Fake linefinder for Sphinx.
try:
    import taskinit
    import asap
    from asap.asaplinefind import linefinder
except:
    print "WARNING: No ASAP; ASAPLineFinder cannot function."
    class linefinder(object):
        def __init__(self):
            pass
    class tb(object):
        def __init__(self):
            pass
        def create(self):
            return


class ASAPSegmentFinder(linefinder):
    """ The AdmitLineFinder class inherits from the asap linefinder class.
        It takes a spectrum (list, CubeSpectrum_BDP, or CubeStats_BDP) and turns
        it into a scantable. The scantable is then search for spectral lines, 
        with the given parameters.

        Parameters
        ----------
        name : string
            Name of the temporary scantable file.
            Default: "".

        spec : various
            Input spectrum, can be a list, CubeSpectrum_BDP, or CubeStats_BDP.
            Default: None.

        Attributes
        ----------
        nchan : int
            Number of spectral channels.

        name : string
            Name of the temporary scantable.

        spectrum : list
            Spectrum to be analyzed.

        lines_merged : list
            Merged list of overlapping lines.

        tb : casa table
            Casa table that is converted to a scantable.

    """

    def __init__(self, **keyval):
        linefinder.__init__(self)
        self.name = "hlinefinder.tmp.asap"
        self.spec = None
        self.vals = ["threshold", "min_nchan", "avg_limit", "box_size", "noise_box",
                     "noise_stat"]
        for v in ["name", "spec"]:
            try:
                setattr(self, v, keyval[v])
            except KeyError:
                pass
        self.nchan = 0
        if self.spec is not None:
            self.nchan = len(self.spec)
        self.scantab = None
        self.spectrum = []
        self.freq = []
        self.lines_merged = []
        self.tb = taskinit.tbtool()
        self.tb.create()

        # create dummy scantable
        self.init()
        if self.spec is not None:
            self.set_spectrum()
        self.set_options(keyval)

    def __del__(self):
        """
            Destructor
        """
        del self.tb

    def init(self):
        """ Create dummy scantable to work with linefinder.

            Parameters
            ----------
            None

            Returns
            -------
            None

            Notes
            -----
            Should not be directly called.
        """
        # remove old table if it exists
        if os.path.exists(self.name):
            os.system('\\rm -rf %s' % (self.name))
        # set ip a scantable
        s = asap._asap.Scantable(False)
        s._save(self.name)
        del s
        # set up a casa table
        self.tb.open(self.name, nomodify=False)
        self.tb.addrows(1)
        if self.nchan != 0:
            self.tb.putcell('SPECTRA', 0, np.zeros(self.nchan, float))
            self.tb.putcell('FLAGTRA', 0, np.zeros(self.nchan, int))
        self.tb.close()

        # make sure dummy scantable is loaded on memory
        storageorg = asap.rcParams['scantable.storage']
        asap.rcParams['scantable.storage'] = 'memory'
        self.scantab = asap.scantable(self.name, False)
        os.system('\\rm -rf %s' % (self.name))
        asap.rcParams['scantable.storage'] = storageorg

    def set_spectrum(self):
        """ Set the spectrum you want to search for lines. If the input spectrum
            was passed to the constructor there is no need to call this routine.

            Parameters
            ----------
            None

            Returns
            -------
            None
        """
        if isinstance(self.spec, list):
            self.spectrum = self.spec
            self.mask = None
        #elif inspect.isclass(spec) and issubclass(spec, BDPB):
        elif isinstance(self.spec, np.array):
            self.spectrum = self.spec.tolist()
            self.mask = None
        elif isinstance(self.spec, ma.array):
            self.spectrum = self.spec.data.tolist()
            self.mask = self.spec.mask.tolist()
            mask = []
        # initialize some things
        if self.nchan != 0:
            #print 'call init() again'
            self.nchan = len(self.spectrum)
            self.init()
            self.scantab._setspectrum(self.spectrum)
        elif self.nchan != len(self.spectrum):
            #print 'nchan differ, call init() again'
            self.nchan = len(self.spectrum)
            self.init()
            self.scantab._setspectrum(self.spectrum)
            del self.finder
            self.finder = asap._asap.linefinder()
            self.set_options()
        else:
            #print 'set spectrum'
            self.scantab._setspectrum(self.spectrum)
        # set the scantable
        linefinder.set_scan(self, self.scantab)

    def merge_lines(self, lines, frac=0.25):
        """ Merge lines if those are close enough.

            Parameters
            ----------
            lines: list
                line list detected by linefinder algorithm

            frac: float
                Criterion for merge as a fraction of line width for narrower line.
                Default: 0.25

            Returns
            -------
            The new number of lines
        """
        nlines = len(lines) / 2

        #print 'nlines = ', nlines
        if nlines == 0 or nlines == 1:
            return lines

        self.lines_merged = []
        merge = []
        for i in xrange(nlines - 1):
            width = min((lines[2 * i + 1] - lines[2 * i]), 
                        (lines[2 * i + 3] - lines[2 * i + 2]))
            sep = lines[2 * i + 2] - lines[2 * i + 1]
            if sep < width * frac:
                merge.append(True)
            else:
                merge.append(False)
        #print 'merge = ', merge
        if merge.count(True) == 0:
            self.lines_merged = lines
            return nlines
        else:
            self.lines_merged.append(lines[0])
            for i in xrange(len(merge)):
                if merge[i]:
                    continue
                else:
                    self.lines_merged.append(lines[2 * i + 1])
                    self.lines_merged.append(lines[2 * i + 2])
            self.lines_merged.append(lines[2 * nlines - 1])

        return len(self.lines_merged)

    def get_merged_ranges(self):
        """ Get a list of merged line ranges.

            Parameters
            ----------
            None

            Returns
            -------
            List of merged lines
        """
        return self.lines_merged

    def set_options(self, **keyval):
        """ Set the options for the linefinding algorithm.

            Parameters
            ----------
            threshold : float
                A single channel S/N ratio above which the channel is considered 
                to be a detection. Default is sqrt(3), which together with 
                min_nchan=3 gives a 3-sigma criterion.
                Default: sqrt(3)

            min_chan : int
                A minimal number of consequtive channels, which should satisfy
                the threshold criterion to be a detection.
                Default: 3

            avg_limit : int
                A number of consequtive channels not greater than this parameter
                can be averaged to search for broad lines.
                Default: 8

            box_size : float
                A running mean box size specified as a fraction of the total
                spectrum length.
                Default: 0.2

            noise_box : string/float
                Area of the spectrum used to estimate noise stats. Both string
                values and numbers are allowed. Allowed string values:
                'all' use all the spectrum, 
                'box' noise box is the same as running mean/median box
                Numeric values are defined as a fraction from the spectrum size.
                Values should be positive. (noise_box == box_size has the same 
                effect as noise_box = 'box').
                Default: 'all'

            noise_stat : string
                Statistics used to estimate noise, allowed values:
                'mean80' use the 80% of the lowest deviations in the noise box, 
                'median' median of deviations in the noise box
                Default: 'mean80'

            Returns
            -------
            None
        """
        items = {}
        self.threshold = math.sqrt(3)
        for v in self.vals:
            try:
                items[v] = keyval[v]
                if v == "threshold":
                    self.threshold = keyval[v]
            except KeyError:
                pass
        linefinder.set_options(self, **items)

    def makepairs(self, inp):
        """ Method to turn a list into a list of pairs

            Parameters
            ----------
            inp : list
                The list to convert

            Returns
            -------
            List of pairs.
        """
        data = []
        if len(inp) % 2 != 0:
            raise Exception("Input list must have even number of inputs")
        for i in range(0, len(inp), 2):
            data.append([inp[i], inp[i + 1]])
        return data

    def find(self, **keyval):
        """ Method to do the actual searching

            Parameters
            ----------
            merge : Boolean
                Whether or not to merge overlapping lines
                Deafult: False

            Returns
            -------
                tuple containing the frequency ranges, channel ranges, and rms, and mean (forced 0.0)

        """
        self.mask = []
        self.merge = False
        vals = ["mask", "merge"]
        for v in vals:
            try:
                setattr(self, v, keyval[v])
            except KeyError:
                pass
        spec = copy.deepcopy(self.spectrum)
        #print "SP ", len(spec)
        nlines = self.find_lines(mask=self.mask)
        #print "LINES ", nlines
        if nlines == 0:
            if self.freq == []:
                return [], 0.0, 100000.0, 0.0
            return [], 0.0, 100000.0, 0.0
        temp = self.get_ranges(False)
        if self.merge:
            temp = self.merge_lines(temp)
        ranges = self.makepairs(temp)
        # remove line channels from the spectrum
        for r in range(len(ranges) - 1, -1, -1):
            del spec[ranges[r][0]:ranges[r][1] + 1]
        newspec = np.array(spec)
        rms = np.sqrt(np.mean(np.square(newspec)))
        return ranges, rms * self.threshold, rms, 0.0
